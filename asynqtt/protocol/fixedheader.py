from abc import ABC, abstractmethod
import enum
import struct
from typing import Container, Optional
from functools import lru_cache
from dataclasses import dataclass, field


class FlagBits(ABC):

    @abstractmethod
    def bits(self) -> int:
        raise NotImplementedError("Must be implemented by base classes")

@dataclass(frozen=True, init=True)
class PublishFlags(FlagBits):
    dup: int = field(default=0, repr=True, hash=True, init=True)
    qos: int = field(default=0, repr=True, hash=True, init=True)
    retain: int = field(default=0, repr=True, hash=True, init=True)

    def __post_init__(self):
        # Validate input
        self._validate_in(self.dup, (0, 1), "dup")
        self._validate_in(self.qos, (0, 1, 2), "qos")
        self._validate_in(self.retain, (0, 1), "retain")

    @staticmethod
    def _validate_in(value: int, container: Container, attribute: str) -> None:
        if value not in container:
            raise ValueError(f"{attribute} must be in {container} but not {value}")

    def bits(self) -> int:
        return 0 | (self.dup << 3) | (self.qos << 1) | self.retain


class ZeroBits(FlagBits):
    """ Flags for all control packets that return 0 for every bit """
    def bits(self) -> int:
        return 0

class PubrelBits(FlagBits):
    """ Flags for PUBREL packets: 0, 0, 1, 0 """
    def bits(self) -> int:
        return 2  # 0 | 1 << 1

SubscribeBits = UnsubscribeBits = PubrelBits
        

class ControlPacketTypeEnum(enum.IntEnum):
    # Reserved = 0
    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14
    # Reserved = 15


class ProtocolVersion(enum.IntEnum):
    MQTTv31 = 3
    MQTTv311 = 4
    MQTTv5 = 5


@dataclass(frozen=True, repr=True, init=True)
class RemainingLength:
    """
    Represents the size of the data in the MQTT message *not* including the size
    of the fixed header (but *including* the size of the variable header and
    payload if appliable)
    """
    message_size: int = field(repr=True, init=True, hash=True)



@dataclass(init=True, repr=True, frozen=True)
class ControlPacket:
    flags: FlagBits = field(default_factory=ZeroBits, repr=False, hash=True, init=True)
    type: ControlPacketTypeEnum = field(repr=True, hash=True, init=False)

    def flag_bits(self) -> int:
        return self.flags.bits()


@dataclass(init=True, repr=True, frozen=True)
class PublishControlPacket(ControlPacket):
    type: ControlPacketTypeEnum = field(default=ControlPacketTypeEnum.PUBLISH, repr=True, hash=True, init=False)
    flags: PublishFlags = field(default_factory=PublishFlags, init=True, hash=True, repr=True)


@dataclass(init=True, repr=True, frozen=True)
class PubrelControlPacket(ControlPacket):
    type: ControlPacketTypeEnum = field(default=ControlPacketTypeEnum.PUBREL, repr=True, hash=True, init=False)
    flags: FlagBits = field(default_factory=PubrelBits, repr=False, hash=True, init=True)


@dataclass(init=True, repr=True, frozen=True)
class SubscribeControlPacket(ControlPacket):
    type: ControlPacketTypeEnum = field(default=ControlPacketTypeEnum.SUBSCRIBE, repr=True, hash=True, init=False)
    flags: FlagBits = field(default_factory=SubscribeBits, repr=False, hash=True, init=True)
