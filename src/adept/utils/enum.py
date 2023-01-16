import enum 

class Enum(enum.EnumMeta): 
    # Enum extended to allow x in Y
    def __contains__(cls, item): 
        return any(x.value == item for x in cls.__members__.values())