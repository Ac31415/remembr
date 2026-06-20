from dataclasses import dataclass
import inspect
import json

@dataclass
class MemoryItem:
    caption: str  # Will be JSON string containing all robots' captions
    time: float
    position: list
    theta: float
    robot_id: str  # Will be comma-separated list of robot IDs
    audio_caption: str = None
    detection_results: dict = None
    robot_data: str = None  # JSON string containing detailed per-robot data

    @classmethod
    def from_dict(cls, dict_input):      
        return cls(**{
            k: v for k, v in dict_input.items() 
            if k in inspect.signature(cls).parameters
        })
    
    def __post_init__(self):
        if self.caption is None:
            self.caption = ''
        if self.audio_caption is None:
            self.audio_caption = ''
        if self.detection_results is None:
            self.detection_results = {}
        if self.robot_id is None:
            self.robot_id = 'unknown'
        if self.robot_data is None:
            self.robot_data = '{}'
    
    def get_robot_data(self):
        """Parse robot_data JSON string into dict"""
        if isinstance(self.robot_data, str):
            try:
                return json.loads(self.robot_data)
            except:
                return {}
        return self.robot_data if self.robot_data else {}


class Memory:

    def insert(self, item: MemoryItem):
        raise NotImplementedError

    def get_working_memory(self) -> list[MemoryItem]:
        raise NotImplementedError

    def search_by_position(self, query: tuple) -> list[MemoryItem]:
        raise NotImplementedError

    def search_by_time(self, hms_time_query: str) -> list[MemoryItem]:
        raise NotImplementedError

    def search_by_text(self, query: str) -> list[MemoryItem]:
        raise NotImplementedError
    
    def search_by_robot(self, robot_id: str) -> list[MemoryItem]:
        raise NotImplementedError

    def memory_to_string(self, memory_list: list[MemoryItem]) -> str:
        raise NotImplementedError
