from dataclasses import dataclass, asdict
import json
import datetime, time
from time import strftime, localtime
from typing import Any, List, Optional, Tuple
from langchain_core.documents import Document
import numpy as np

from remembr.memory.memory_multimodal import Memory, MemoryItem

from langchain_community.vectorstores import Milvus
from langchain_huggingface import HuggingFaceEmbeddings

from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility


FIXED_SUBTRACT=1721761000 # legacy offset; kept for read-back compatibility only.
# NOTE (schema fix, April 2026):
# Previously `time` was a FLOAT_VECTOR(dim=2) storing `[t - FIXED_SUBTRACT, 0.0]`
# as fp32. Because fp32 has only ~7 decimal digits of precision, once
# `t - FIXED_SUBTRACT` grew past ~1.6e7 (roughly 6 months after the offset
# epoch), consecutive captures 1s apart were rounding to the same float,
# producing duplicate timestamps that jumped in ~4-second steps. The schema
# now stores `time` as a DOUBLE (fp64) with the raw unix timestamp, and uses
# an auto-generated INT64 primary key instead of the manually-set `id =
# str(time.time())` (which was computed at insert time on a background thread
# and was therefore non-monotonic w.r.t. capture order).
#
# Existing collections created with the old schema MUST be dropped before
# using this module (e.g. via the inspector's --reset flag).



class MilvusWrapper:

    def __init__(self, collection_name='test', ip_address='127.0.0.1', port=19530, drop_collection=False):
        self.collection_name = collection_name
        self.collection = self.connect_to_milvus_collection(collection_name, 1024, address=ip_address, port=port, drop_collection=drop_collection)


    def drop_collection(self):
        utility.drop_collection(self.collection_name)

    def connect_to_milvus_collection(self, collection_name, dim, address='127.0.0.1', port=19530, drop_collection=False):
        connections.connect(host=address, port=port)
        
        if drop_collection:
            utility.drop_collection(collection_name)
        
        fields = [
            # Auto-generated INT64 primary key; not user-writable. Replaces the
            # former VARCHAR `id` that was manually set to str(time.time()) at
            # insert time (which was non-monotonic w.r.t. capture order).
            FieldSchema(name='pk', dtype=DataType.INT64, description='auto primary key', is_primary=True, auto_id=True),
            FieldSchema(name='text_embedding', dtype=DataType.FLOAT_VECTOR, description='embedding vectors', dim=dim),
            FieldSchema(name='position', dtype=DataType.FLOAT_VECTOR, description='position of robot', dim=3),
            FieldSchema(name='theta', dtype=DataType.FLOAT, description='rotation of robot', dim=1),
            # Full-precision unix capture time (fp64). Replaces the former
            # FLOAT_VECTOR(dim=2) representation which lost sub-4-second
            # resolution after the FIXED_SUBTRACT epoch.
            FieldSchema(name='time', dtype=DataType.DOUBLE, description='unix capture time (seconds, fp64)'),
            FieldSchema(name='caption', dtype=DataType.VARCHAR, description='caption string', max_length=3000),
            FieldSchema(name='audio_caption', dtype=DataType.VARCHAR, description='audio caption string', max_length=3000),
        ]
        schema = CollectionSchema(fields=fields, description='text image search')
        collection = Collection(name=collection_name, schema=schema)

        # create IVF_FLAT index for collection.
        index_params = {
            'metric_type':'L2',
            'index_type':"IVF_FLAT",
            'params':{"nlist":1024}
        }
        collection.create_index(field_name="text_embedding", index_params=index_params)

        index_params = {
            'metric_type':'L2',
            'index_type':"IVF_FLAT",
            'params':{"nlist":2}
        }
        collection.create_index(field_name="position", index_params=index_params)

        # `time` is now a scalar DOUBLE; use a scalar STL_SORT index so
        # range queries like `time >= X and time <= Y` are fast.
        collection.create_index(field_name="time",
                                index_params={"index_type": "STL_SORT"})

        return collection
    
    def insert(self, data_list):
        res = self.collection.insert(data_list)

    def search(self, data):

        self.collection.load()

        BATCH_SIZE = 2
        LIMIT = 10

        param = {
            "metric_type": "L2",
            "params": {
                "nprobe": 1024,
            }
        }

        res = self.collection.search(
            data=[data],
            anns_field="text_embedding",
            param=param,
            batch_size=BATCH_SIZE,
            limit=LIMIT,
            output_fields=["pk", "text_embedding"]
        )

        return res




class MilvusMemory(Memory):


    def __init__(self, db_collection_name: str, db_ip='127.0.0.1', db_port=19530, time_offset=FIXED_SUBTRACT):

        self.db_collection_name = db_collection_name
        self.db_ip = db_ip
        self.db_port = db_port
        self.time_offset = time_offset

        self.embedder = HuggingFaceEmbeddings(model_name='mixedbread-ai/mxbai-embed-large-v1')

        self.working_memory = []

        self.reset(drop_collection=False)


    def insert(self, item: MemoryItem, text_embedding=None):
        memory_dict = asdict(item)
        # No manual id: the `pk` field is auto-generated by Milvus.

        if text_embedding is None:
            # FIXED: Combine visual and audio captions for embedding
            combined_text = memory_dict['caption']
            if memory_dict.get('audio_caption') and memory_dict['audio_caption'].strip():
                combined_text += f" Audio: {memory_dict['audio_caption']}"

            text_embedding = self.embedder.embed_query(combined_text)
            print(f"[Memory] Creating embedding for combined text: {combined_text[:100]}...")

        # Store the raw unix capture time as fp64; full sub-millisecond
        # precision is preserved.
        memory_dict['time'] = float(memory_dict['time'])
        memory_dict['text_embedding'] = text_embedding
        
        # Ensure audio_caption field exists (for backward compatibility)
        if 'audio_caption' not in memory_dict:
            memory_dict['audio_caption'] = ''

        self.milv_wrapper.insert([memory_dict])
        print(f"[Memory] Inserted memory with audio_caption: '{memory_dict.get('audio_caption', '')[:50]}...'")

    def get_working_memory(self) -> list[MemoryItem]:
        return self.working_memory

    def reset(self, drop_collection=True):

        if drop_collection:
            print("Resetting memory. We are dropping the current collection")

        self.milv_wrapper = MilvusWrapper(self.db_collection_name, self.db_ip, self.db_port, drop_collection=drop_collection)

        text_vector_db = Milvus(
            self.embedder,
            connection_args={"host": self.db_ip, "port": self.db_port},
            collection_name=self.db_collection_name,
            vector_field='text_embedding',
            text_field='caption',
        )
        self.text_retriever = text_vector_db.as_retriever(search_kwargs={"k": 5})


        self.position_vector_db = Milvus(
            self.embedder, # we will ignore this
            connection_args={"host": self.db_ip, "port": self.db_port},
            collection_name=self.db_collection_name,
            vector_field='position',
            text_field='caption',
        )

        # `time` is no longer a vector field; scalar range queries are used
        # instead (see `search_by_time`). We keep a direct handle to the
        # raw pymilvus Collection for those queries.
        self.time_collection = self.milv_wrapper.collection


    def search_by_position(self, query: tuple) -> str:
        # docs = pos_db.similarity_search_by_vector(np.array(query))
        docs = similarity_search_with_score_by_vector(self.position_vector_db, np.array(query).astype(float))

        self.working_memory += docs 

        docs = self.memory_to_string(docs)

        """Look up things online."""
        return docs

    def search_by_time(self, hms_time: str, k: int = 4, window_seconds: float = 3600.0) -> str:
        """Return the ``k`` memory entries whose capture time is closest to
        ``hms_time`` (an ``HH:MM:SS`` or ``MM/DD/YYYY HH:MM:SS`` string).

        Uses a scalar range query on the new DOUBLE ``time`` field — this is
        exact, unlike the former fp32 vector similarity search.
        """
        # Parse the HMS input against the session date (derived from
        # self.time_offset, which still marks an approximate session epoch).
        ref_struct = localtime(self.time_offset)
        mdy_date = strftime('%m/%d/%Y', ref_struct)
        template = "%m/%d/%Y %H:%M:%S"

        try:
            datetime.datetime.strptime(hms_time, template)
            full_str = hms_time.strip()
        except ValueError:
            full_str = f"{mdy_date} {hms_time.strip()}"

        query_epoch = time.mktime(
            datetime.datetime.strptime(full_str, template).timetuple())

        self.milv_wrapper.collection.load()
        lo = query_epoch - window_seconds
        hi = query_epoch + window_seconds
        raw = self.milv_wrapper.collection.query(
            expr=f"time >= {lo} and time <= {hi}",
            output_fields=["caption", "audio_caption", "position", "theta", "time"],
            limit=1024,
        )
        # Sort by absolute distance to the query time; return the top k.
        raw.sort(key=lambda r: abs(float(r.get("time", 0.0)) - query_epoch))
        raw = raw[:k]

        docs = [Document(page_content=r.get("caption", ""), metadata=r) for r in raw]
        self.working_memory += docs
        return self.memory_to_string(docs)



    def search_by_text(self, query: str) -> str:
        """Enhanced text search that includes audio captions"""
        print(f"[Memory] Searching for: '{query}'")
        
        # Search both visual and audio content
        docs = self.text_retriever.invoke(query)
        
        print(f"[Memory] Found {len(docs)} documents")
        for i, doc in enumerate(docs[:3]):  # Debug first 3 results
            audio_caption = doc.metadata.get('audio_caption', '')
            print(f"[Memory] Doc {i}: Visual='{doc.page_content[:50]}...', Audio='{audio_caption[:50]}...'")
        
        self.working_memory += docs
        docs = self.memory_to_string(docs)
        
        return docs
    

    ### Doc formatting for the last LLM
    def memory_to_string(self, memory_list: list[MemoryItem], ref_time: float=None):
        out_string = ""
        for doc in memory_list:
            raw_t = doc.metadata['time']
            # Back-compat: an old collection may still return `time` as a
            # length-2 vector [t_offset, 0]; a new collection returns a scalar
            # fp64 unix timestamp.
            if isinstance(raw_t, (list, tuple)):
                t = float(raw_t[0])
                if t < 1_000_000_000:  # looks like offset-subtracted
                    t += self.time_offset
            else:
                t = float(raw_t)
            t = localtime(t)
            t = strftime('%Y-%m-%d %H:%M:%S', t)

            s = f"At time={t}, the robot was at an average position of {np.array(doc.metadata['position']).round(3).tolist()}."
            s += f"The robot saw the following: {doc.page_content}"
            
            # Add audio caption if available
            audio_caption = doc.metadata.get('audio_caption', '')
            if audio_caption and audio_caption.strip():
                s += f" Audio: {audio_caption}"
            
            s += "\n\n"
            out_string += s
        return out_string
    
    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """
        Enhanced search method that includes audio captions with fallback strategies
        """
        try:
            print(f"[Memory] Enhanced search for: '{query}' (limit: {limit})")
            
            # Use the text retriever to search (this searches the combined embeddings)
            docs = self.text_retriever.invoke(query)
            
            print(f"[Memory] Text retriever returned {len(docs)} documents")
            
            # Convert documents to MemoryItem objects
            memory_items = []
            for i, doc in enumerate(docs[:limit]):
                try:
                    audio_caption = doc.metadata.get('audio_caption', '')
                    print(f"[Memory] Processing doc {i}: audio_caption='{audio_caption[:30]}...'")
                    
                    raw_t = doc.metadata.get('time', 0.0)
                    if isinstance(raw_t, (list, tuple)):
                        raw_t = raw_t[0] if raw_t else 0.0
                    memory_item = MemoryItem(
                        caption=doc.page_content,
                        position=doc.metadata.get('position', [0.0, 0.0, 0.0]),
                        theta=doc.metadata.get('theta', 0.0),
                        time=float(raw_t),
                        audio_caption=audio_caption,
                    )
                    memory_items.append(memory_item)
                    
                    print(f"[Memory] Added memory item: visual='{memory_item.caption[:30]}...', audio='{memory_item.audio_caption[:30]}...'")
                    
                except Exception as e:
                    print(f"[Memory] Error converting document {i} to MemoryItem: {e}")
                    continue
            
            print(f"[Memory] Returning {len(memory_items)} memory items")
            return memory_items
            
        except Exception as e:
            print(f"[Memory] Search failed: {e}")
            import traceback
            traceback.print_exc()
            return []


# NOTE: This version of the code returns the vector
def similarity_search_with_score_by_vector(
        pos_db,
        embedding: List[float],
        k: int = 4,
        param: Optional[dict] = None,
        expr: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Perform a search on a query string and return results with score.

        For more information about the search parameters, take a look at the pymilvus
        documentation found here:
        https://milvus.io/api-reference/pymilvus/v2.2.6/Collection/search().md

        Args:
            embedding (List[float]): The embedding vector being searched.
            k (int, optional): The amount of results to return. Defaults to 4.
            param (dict): The search params for the specified index.
                Defaults to None.
            expr (str, optional): Filtering expression. Defaults to None.
            timeout (float, optional): How long to wait before timeout error.
                Defaults to None.
            kwargs: Collection.search() keyword arguments.

        Returns:
            List[Tuple[Document, float]]: Result doc and score.
        """
        if pos_db.col is None:
            print("No existing collection to search.")
            return []

        if param is None:
            param = pos_db.search_params

        # Determine result metadata fields with PK.
        output_fields = pos_db.fields[:]
        # output_fields.remove(pos_db._vector_field) # NOTE: Only thing removed
        timeout = pos_db.timeout or timeout
        # Perform the search.
        res = pos_db.col.search(
            data=[embedding],
            anns_field=pos_db._vector_field,
            param=param,
            limit=k,
            expr=expr,
            output_fields=output_fields,
            timeout=timeout,
            **kwargs,
        )
        # Organize results.
        ret = []
        for result in res[0]:
            data = {x: result.entity.get(x) for x in output_fields}
            doc = pos_db._parse_document(data)
            pair = (doc, result.score)
            ret.append(pair)

        return [doc for doc, _ in ret]