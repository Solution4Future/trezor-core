# Automatically generated by pb2py
from protobuf import protobuf as p
from .HDNodeType import HDNodeType
t = p.MessageType('PublicKey')
t.wire_type = 12
t.add_field(1, 'node', p.EmbeddedMessage(HDNodeType), flags=p.FLAG_REQUIRED)
t.add_field(2, 'xpub', p.UnicodeType)
PublicKey = t