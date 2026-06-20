from dataclasses import dataclass, asdict
import json
import datetime, time
from time import strftime, localtime
from typing import Any, List, Optional, Tuple
from langchain_core.documents import Document
import numpy as np

from remembr.memory.memory_multimodal_multirobot import Memory, MemoryItem

from langchain_community.vectorstores import Milvus
from langchain_huggingface import HuggingFaceEmbeddings

from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility


FIXED_SUBTRACT=1721761000 # legacy offset; kept for read-back compatibility only.
# See docstring in `milvus_memory_multimodal.py` for the schema-fix rationale:
# `time` is now a DOUBLE (full-precision unix seconds) and the primary key is
# an auto-generated INT64, replacing the former fp32 vector time and the
# manually-assigned VARCHAR `id` that was non-monotonic w.r.t. capture order.
# Existing collections must be dropped before using this module.



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
            # Auto-generated INT64 primary key (replaces manually-set VARCHAR id).
            FieldSchema(name='pk', dtype=DataType.INT64, description='auto primary key', is_primary=True, auto_id=True),
            FieldSchema(name='text_embedding', dtype=DataType.FLOAT_VECTOR, description='embedding vectors', dim=dim),
            FieldSchema(name='position', dtype=DataType.FLOAT_VECTOR, description='position of robot', dim=3),
            FieldSchema(name='theta', dtype=DataType.FLOAT, description='rotation of robot', dim=1),
            # Full-precision unix capture time (fp64); replaces fp32 FLOAT_VECTOR.
            FieldSchema(name='time', dtype=DataType.DOUBLE, description='unix capture time (seconds, fp64)'),
            FieldSchema(name='caption', dtype=DataType.VARCHAR, description='caption string', max_length=3000),
            FieldSchema(name='audio_caption', dtype=DataType.VARCHAR, description='audio caption string', max_length=3000),
            FieldSchema(name='detection_results', dtype=DataType.VARCHAR, description='YOLO detection results as JSON', max_length=10000),
            FieldSchema(name='robot_id', dtype=DataType.VARCHAR, description='robot identifier (comma-separated)', max_length=100),
            FieldSchema(name='robot_data', dtype=DataType.VARCHAR, description='per-robot detailed data as JSON', max_length=20000),
        ]
        schema = CollectionSchema(fields=fields, description='multi-robot text image search')
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

        # Scalar STL_SORT index on DOUBLE `time` for fast range queries.
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
        # No manual id: `pk` is auto-generated by Milvus.

        if text_embedding is None:
            # Combine visual and audio captions for embedding
            combined_text = memory_dict['caption']
            if memory_dict.get('audio_caption') and memory_dict['audio_caption'].strip():
                combined_text += f" Audio: {memory_dict['audio_caption']}"

            text_embedding = self.embedder.embed_query(combined_text)
            print(f"[Memory] Creating embedding for robots '{memory_dict.get('robot_id')}': {combined_text[:100]}...")

        # Store the raw unix capture time at full fp64 precision.
        memory_dict['time'] = float(memory_dict['time'])
        memory_dict['text_embedding'] = text_embedding
        
        # Ensure audio_caption field exists
        if 'audio_caption' not in memory_dict:
            memory_dict['audio_caption'] = ''
        
        # Ensure robot_id field exists
        if 'robot_id' not in memory_dict:
            memory_dict['robot_id'] = 'unknown'
        
        # Convert detection_results dict to JSON string for storage
        if 'detection_results' in memory_dict:
            if isinstance(memory_dict['detection_results'], dict):
                memory_dict['detection_results'] = json.dumps(memory_dict['detection_results'])
            elif memory_dict['detection_results'] is None:
                memory_dict['detection_results'] = '{}'
        else:
            memory_dict['detection_results'] = '{}'
        
        # Convert robot_data to JSON string for storage
        if 'robot_data' in memory_dict:
            if isinstance(memory_dict['robot_data'], dict):
                memory_dict['robot_data'] = json.dumps(memory_dict['robot_data'])
            elif memory_dict['robot_data'] is None:
                memory_dict['robot_data'] = '{}'
        else:
            memory_dict['robot_data'] = '{}'

        self.milv_wrapper.insert([memory_dict])
        print(f"[Memory] Inserted memory for robots '{memory_dict['robot_id']}' with audio: '{memory_dict.get('audio_caption', '')[:50]}...'")

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

        # `time` is a scalar DOUBLE now; keep a direct Collection handle
        # for scalar range queries (see `search_by_time`).
        self.time_collection = self.milv_wrapper.collection


    def search_by_position(self, query: tuple) -> str:
        docs = similarity_search_with_score_by_vector(self.position_vector_db, np.array(query).astype(float))
        self.working_memory += docs 
        docs = self.memory_to_string(docs)
        return docs

    def search_by_time(self, hms_time: str, k: int = 4, window_seconds: float = 3600.0) -> str:
        """Return the ``k`` memory entries whose capture time is closest to
        ``hms_time`` (``HH:MM:SS``). Uses a scalar range query on the DOUBLE
        ``time`` field — exact, unlike the former fp32 vector similarity.
        """
        time_epoch = datetime.datetime.strptime(hms_time, '%H:%M:%S').timestamp()

        self.milv_wrapper.collection.load()
        lo = time_epoch - window_seconds
        hi = time_epoch + window_seconds
        raw = self.milv_wrapper.collection.query(
            expr=f"time >= {lo} and time <= {hi}",
            output_fields=["caption", "audio_caption", "detection_results",
                           "position", "theta", "time", "robot_id", "robot_data"],
            limit=1024,
        )
        raw.sort(key=lambda r: abs(float(r.get("time", 0.0)) - time_epoch))
        raw = raw[:k]

        docs = []
        for r in raw:
            time_readable = strftime('%H:%M:%S',
                                     localtime(float(r.get("time", 0.0))))
            r_display = dict(r)
            r_display['time'] = time_readable
            docs.append((Document(page_content=r.get("caption", ""),
                                  metadata=r_display), 0.0))

        self.working_memory += docs
        return self.memory_to_string(docs)

    def search_by_robot(self, robot_id: str) -> str:
        """Search memories by robot ID"""
        self.milv_wrapper.collection.load()
        
        results = self.milv_wrapper.collection.query(
            expr=f'robot_id == "{robot_id}"',
            output_fields=["caption", "audio_caption", "detection_results", "time", "position", "theta", "robot_id"],
            limit=100
        )

        # Convert results to MemoryItem objects
        memory_items = []
        for result in results:
            # Deserialize detection_results from JSON
            detection_results = {}
            if 'detection_results' in result and result['detection_results']:
                try:
                    detection_results = json.loads(result['detection_results'])
                except:
                    detection_results = {}

            # `time` is now a scalar DOUBLE. Back-compat: fall back to the
            # legacy list form if reading an old collection.
            raw_t = result.get('time', 0.0)
            if isinstance(raw_t, (list, tuple)):
                raw_t = float(raw_t[0]) if raw_t else 0.0
                if raw_t < 1_000_000_000:
                    raw_t += self.time_offset
            else:
                raw_t = float(raw_t)

            memory_item = MemoryItem(
                caption=result.get('caption', ''),
                time=raw_t,
                position=result.get('position', [0.0, 0.0, 0.0]),
                theta=result.get('theta', 0.0),
                robot_id=result.get('robot_id', 'unknown'),
                audio_caption=result.get('audio_caption', ''),
                detection_results=detection_results
            )
            memory_items.append(memory_item)
        
        return self.memory_to_string_items(memory_items)

    def search_by_text(self, query: str) -> str:
        text_embedding = self.embedder.embed_query(query)
        docs = similarity_search_with_score_by_vector(self.text_retriever.vectorstore, text_embedding)

        docs_new = []
        for doc, score in docs:
            raw_t = doc.metadata.get('time')
            if raw_t is not None:
                if isinstance(raw_t, (list, tuple)):
                    t_val = float(raw_t[0]) if raw_t else 0.0
                    if t_val < 1_000_000_000:  # legacy offset-subtracted form
                        t_val += self.time_offset
                else:
                    t_val = float(raw_t)
                doc.metadata['time'] = strftime('%H:%M:%S', localtime(t_val))
            docs_new.append((doc, score))

        docs = docs_new
        self.working_memory += docs
        docs = self.memory_to_string(docs)
        return docs



    ### Doc formatting for the last LLM
    def memory_to_string(self, memory_list: list[MemoryItem], ref_time: float=None):
        memory_strings = []
        for doc, score in memory_list:
            pos = doc.metadata['position']
            caption_text = doc.page_content
            audio_caption = doc.metadata.get('audio_caption', '')
            robot_id = doc.metadata.get('robot_id', 'unknown')
            
            # Deserialize detection_results
            detection_results = {}
            if 'detection_results' in doc.metadata and doc.metadata['detection_results']:
                try:
                    detection_results_str = doc.metadata['detection_results']
                    detection_results = json.loads(detection_results_str) if isinstance(detection_results_str, str) else detection_results_str
                except:
                    detection_results = {}
            
            time_mem = doc.metadata['time']

            # Build memory string with robot ID
            memory_str = f"[Robot: {robot_id}] At position ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}) at time {time_mem}, I saw: {caption_text}"
            if audio_caption:
                memory_str += f" and heard: {audio_caption}"
            if detection_results and detection_results.get('classes'):
                num_objects = len(detection_results['classes'])
                memory_str += f" (detected {num_objects} objects)"
            
            memory_strings.append(memory_str)

        return '\n'.join(memory_strings)
    
    def memory_to_string_items(self, memory_list: list[MemoryItem], ref_time: float=None):
        """Convert MemoryItem list to string"""
        memory_strings = []
        for item in memory_list:
            time_readable = strftime('%H:%M:%S', localtime(item.time))
            memory_str = f"[Robot: {item.robot_id}] At position ({item.position[0]:.2f}, {item.position[1]:.2f}, {item.position[2]:.2f}) at time {time_readable}, I saw: {item.caption}"
            if item.audio_caption:
                memory_str += f" and heard: {item.audio_caption}"
            if item.detection_results and item.detection_results.get('classes'):
                num_objects = len(item.detection_results['classes'])
                memory_str += f" (detected {num_objects} objects)"
            memory_strings.append(memory_str)
        
        return '\n'.join(memory_strings)


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
    """Return docs most similar to embedding vector with scores.

    Args:
        embedding: Embedding to look up documents similar to.
        k: Number of Documents to return. Defaults to 4.
        param: Search parameters for Milvus. Defaults to None.
        expr: Filtering expression. Defaults to None.
        timeout: Timeout for the search. Defaults to None.
        kwargs: Additional keyword arguments.

    Returns:
        List of Documents most similar to the embedding with scores.
    """
    if param is None:
        param = pos_db.search_params

    from pymilvus import Collection

    col = Collection(pos_db.collection_name)
    col.load()
    
    # Determine search params by vector field.
    if pos_db.vector_field != pos_db._metadata_field:
        output_fields = pos_db.fields[:]
    else:
        output_fields = [pos_db.primary_field, pos_db._metadata_field]
    output_fields.append(pos_db._vector_field)

    # Perform the search.
    res = col.search(
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
        meta = {x: result.entity.get(x) for x in output_fields}
        if pos_db.vector_field in meta:
            vector = meta.pop(pos_db.vector_field)
        else:
            vector = []

        doc = Document(page_content=meta.pop(pos_db._text_field), metadata=meta)
        pair = (doc, result.score)
        ret.append(pair)

    return ret
