# db/repository.py
from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    async def get_categories(self):
        pass
