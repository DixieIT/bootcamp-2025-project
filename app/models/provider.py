from enum import Enum

class Provider(Enum):
    OPENAI = 'openai'
    GOOGLE = 'google'
    MOCK = 'mock'