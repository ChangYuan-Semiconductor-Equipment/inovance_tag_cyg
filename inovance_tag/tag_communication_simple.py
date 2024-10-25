"""Simple instance."""
from inovance_tag.tag_communication import TagCommunication
from inovance_tag.tag_type_enum import TagTypeEnum

if __name__ == '__main__':
    tag = TagCommunication("127.0.0.1")  # 实例化标签通讯实例
    tag.communication_open()  # 通过标签通讯实例打开plc通讯, 读和写之前必须要执行这个操作

    tag.execute_write("tag_name_value", TagTypeEnum.INT.value, 1)  # 写入 int
    tag.execute_write("tag_name_value", TagTypeEnum.STRING.value, "string_value")  # 写入 str
    tag.execute_write("tag_name_value", TagTypeEnum.BOOL.value, True)  # 写入 bool

    tag.execute_read("tag_name_value", TagTypeEnum.INT.value)  # 读取 int 值
    tag.execute_read("tag_name_value", TagTypeEnum.STRING.value)  # 读取 string 值
    tag.execute_read("tag_name_value", TagTypeEnum.BOOL.value)  # 读取 bool 值
