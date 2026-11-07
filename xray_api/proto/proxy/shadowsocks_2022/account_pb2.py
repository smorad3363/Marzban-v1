"""Minimal generated-compatible SS2022 Account protobuf for Xray gRPC.

The committed SS2022 config_pb2 predates Account; this separate descriptor
registers the upstream xray.proxy.shadowsocks_2022.Account{key=1} type.
"""
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

_proto = descriptor_pb2.FileDescriptorProto()
_proto.name = "proxy/shadowsocks_2022/account_marzban.proto"
_proto.package = "xray.proxy.shadowsocks_2022"
_proto.syntax = "proto3"
_message = _proto.message_type.add()
_message.name = "Account"
_field = _message.field.add()
_field.name = "key"
_field.number = 1
_field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
_field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
DESCRIPTOR = descriptor_pool.Default().AddSerializedFile(_proto.SerializeToString())
Account = message_factory.GetMessageClass(DESCRIPTOR.message_types_by_name["Account"])
