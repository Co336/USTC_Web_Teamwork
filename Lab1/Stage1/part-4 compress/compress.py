import pickle
import shelve
from pympler import asizeof

file_book_hash_list = "part-4 compress\data0\\book_hash_list.pkl"
file_movie_hash_list = "part-4 compress\data0\\movie_hash_list.pkl"

# 将hash表载入内存
def hash_load(file_hash_list):
    with open(file_hash_list, 'rb') as f:
        hash_list = pickle.load(f)
    return hash_list

# 可变长度编码
def varint_encode(value):
    encoded = []
    while value > 127:
        encoded.append((value & 0x7F) | 0x80)  # 取低7位，加上继续位
        value >>= 7
    encoded.append(value)  # 最后一字节，无继续位
    return bytes(encoded)

# 可变长度解码
def varint_decode(data):
    shift = 0
    result = 0
    for index, byte in enumerate(data):
        result |= (byte & 0x7F) << shift
        shift += 7
        if not (byte & 0x80):  # 检测无继续位
            return result, index + 1  # 返回值和读取字节数
    raise ValueError("Incomplete Varint data")

# 对文档id采用间距可变长编码进行压缩
def compress_ids(id_list):
    int_ids = list(map(int, id_list))  # 将字符串转换为整数
    base_id = int_ids[0]  # 记录基准ID
    gaps = [int_ids[i] - int_ids[i - 1] for i in range(1, len(int_ids))]  # 计算差值
    compressed = varint_encode(base_id)  # 编码基准ID
    for gap in gaps:
        compressed += varint_encode(gap)  # 编码间距
    return compressed

# 文档id解压缩
def decompress_ids(compressed):
    index = 0
    base_id, offset = varint_decode(compressed[index:])  # 解码基准ID
    index += offset
    gaps = []
    while index < len(compressed):
        gap, offset = varint_decode(compressed[index:])
        gaps.append(gap)
        index += offset
    ids = [base_id]  # 构建还原的 ID 列表
    for gap in gaps:
        ids.append(ids[-1] + gap)  # 通过差值还原完整ID
    return list(map(str, ids))

def compress_terms(term_hash_table):
    """
    压缩词项哈希表
    :param term_hash_table: 原始哈希表，格式 [[[term_name, inverted_index_pointer], ...], [], ...]
    :return: 压缩后的字符串块和指针信息
    """
    block = bytearray()  # 用于存储所有词项的字符串块
    pointers = []  # 存储每 4 个词项的指针
    temp_group = []  # 临时存储当前组的倒排索引指针
    pos = 0 # 存储位置信息

    for term_group in term_hash_table:
        if not term_group:  # 空列表直接跳过
            pointers.append(())
            continue

        for term, pointer in term_group:
            encoded_term = term.encode("gb18030")  # 将词项编码为字节
            length = len(encoded_term)  # 词项长度
            block.extend(bytes([length]))  # 添加长度（1 字节）
            block.extend(encoded_term)  # 添加词项
            temp_group.append(pointer)  # 添加倒排索引指针

        # 完成当前哈希组，存储指针并清空临时组
        if len(temp_group) > 0:
            pointers.append((pos, temp_group[:]))
            pos = len(block)
            temp_group.clear()

    return block, pointers

def decompress_terms(block, pointers):
    """
    解压缩词项哈希表
    :param block: 压缩后的字符串块
    :param pointers: 每组词项的指针信息
    :return: 解压后的哈希表
    """
    term_hash_table = []

    for tuple in pointers:
        if tuple:
            start_pos = tuple[0]
            group_pointers = tuple[1]
        else:  # 空组
            term_hash_table.append([])
            continue

        pos = start_pos
        group = []
        for pointer in group_pointers:
            length = block[pos]  # 读取词项长度
            pos += 1
            term = block[pos:pos + length].decode("gb18030")  # 读取词项内容
            pos += length
            group.append([term, pointer])
        term_hash_table.append(group)

    return term_hash_table


def term_compress():
    # 哈希表载入
    book_term_hash_table = hash_load(file_book_hash_list)
    movie_term_hash_table = hash_load(file_movie_hash_list)

    # 压缩
    compressed_book_block, compressed_book_pointers = compress_terms(book_term_hash_table)
    compressed_movie_block, compressed_movie_pointers = compress_terms(movie_term_hash_table)
    print("压缩前后书籍hash表大小变化:")
    print(asizeof.asizeof(book_term_hash_table))
    print(asizeof.asizeof(compressed_book_block)+asizeof.asizeof(compressed_book_pointers))
    print("压缩前后电影hash表大小变化:")
    print(asizeof.asizeof(movie_term_hash_table))
    print(asizeof.asizeof(compressed_movie_block)+asizeof.asizeof(compressed_movie_pointers))

    # 存储到文件
    with open("part-4 compress\data1\compressed_book_terms.pkl", "wb") as f:
        pickle.dump((compressed_book_block, compressed_book_pointers), f)

    with open("part-4 compress\data1\compressed_movie_terms.pkl", "wb") as f:
        pickle.dump((compressed_movie_block, compressed_movie_pointers), f)
    # 从文件读取
    with open("part-4 compress\data1\compressed_movie_terms.pkl", "rb") as f:
        loaded_block, loaded_pointers = pickle.load(f)
        loaded_table = decompress_terms(loaded_block, loaded_pointers)
        print("从文件解压后的词项哈希表：", loaded_table)


# 书籍的压缩前后文件
book_input_shelve_file = "part-4 compress\data0\\book_index_list"
book_output_shelve_file = "part-4 compress\data1\compressed_book_index"
# 电影的压缩前后文件
movie_input_shelve_file = "part-4 compress\data0\\movie_index_list"
movie_output_shelve_file = "part-4 compress\data1\compressed_movie_index"
# 索引压缩
def index_compress(input_shelve_file,output_shelve_file):
    # 读取未压缩的文件并进行压缩存储
    size = c_size = 0
    with shelve.open(input_shelve_file) as input_db, shelve.open(output_shelve_file) as output_db:
        for key in input_db:  # 遍历所有键
            id_list = input_db[key]  # 读取 ID 列表
            compressed_index = [compress_ids(id_list[0]),compress_ids(id_list[1]),id_list[2]]  # 压缩 ID 列表
            output_db[key] = compressed_index  # 存储到新的 shelve 文件
            # 计算压缩前后内存大小
            size += asizeof.asizeof(id_list)
            c_size += asizeof.asizeof(compressed_index)
    print(f"索引数据已从 {input_shelve_file} 压缩并存储到 {output_shelve_file}")
    print(f"索引压缩前大小:{size}")
    print(f"索引压缩后大小:{c_size}")


index_compress(book_input_shelve_file,book_output_shelve_file)
index_compress(movie_input_shelve_file,movie_output_shelve_file)