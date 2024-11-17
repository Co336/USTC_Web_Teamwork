import pandas as pd
import pickle
import shelve
import math

def hash_function(input_str):
    hash_value = 0
    prime_number = 31  # 质数因子，帮助避免哈希冲突
    max_hash_value = 81919  # 哈希表大小（质数大小）
    
    for char in input_str:
        # 获取字符的GB18030编码
        encoded_char = char.encode('gb18030')
        
        # 将字符的每个字节的值与hash_value结合
        for byte in encoded_char:
            hash_value = hash_value * prime_number + byte
            
            # 使用位操作防止溢出
            hash_value &= 0xFFFFFFFFFFFFFFFF  # 限制哈希值范围，确保64位
    
    # 最终的哈希值映射到[0, max_hash_value]范围
    hash_value = hash_value % max_hash_value
    
    return hash_value


file_book_keywords_csv = "jieba\data\\book_keywords.csv"
file_movie_keywords_csv = "jieba\data\movie_keywords.csv"

# 建立顺序token索引表
def csv_to_index_table(csvfile):
    index_table = {}
    content = pd.read_csv(csvfile, delimiter=',', header=None, index_col=False)
    idlist = content[0].values
    tokenlist = content[1].values
    for i in range(1,len(idlist)):
        tokens = eval(tokenlist[i])
        for token in tokens:
            if not index_table.get(token):
                index_table[token] = [idlist[i]]
            else:
                if idlist[i] not in index_table[token]:
                    index_table[token].append(idlist[i])
    return index_table

# 索引表排序
def sort_index_table(index_table):
    sorted_index_table = {}
    keys_encoded = [k.encode('gb18030') for k in index_table.keys()]
    keys_encoded.sort()
    keys_sorted = [k.decode('gb18030') for k in keys_encoded]
    for key in keys_sorted:
        sorted_index_table[key] = index_table[key]
        sorted_index_table[key].sort()
    return sorted_index_table

# 建立跳表指针，添加词项的文档频率
# 注:此处跳表的结构是建立一个新的列表作为索引,按每跳step个选取原列表元素,查询时同时与多个列表进行比较即可.
#    目前是单层跳表,实际上,多层跳表也只需增加列表的数量即可,但这会使搜索算法复杂度增加,待跳表结构改进后再考虑建立多层跳表.   
def skip_list_build(index_table):
    skip_list = []
    for key in index_table.keys():
        # 以根号L为步长建立跳表
        step = math.floor(math.sqrt(len(index_table[key]))) 
        for i in range(1,len(index_table[key])//step+1):
            skip_list.append(index_table[key][step*i-1])
        index_table[key] = [index_table[key],skip_list,len(index_table[key])]
        skip_list = []
    return index_table

# 索引表存储优化(哈希存储)
def index_table_storage(index_table,file_index_list):
    # 将词项和索引表分别存于两个文件中，通过hash表查找词项，再根据词项索引在索引表中查找
    # 将词项放进pkl文件，方便直接载入内存，索引表放入shelve文件中，方便根据索引部分查询
    with shelve.open(file_index_list) as db:
        for key in index_table.keys():
            db[str(key)] = index_table[key]  # 使用索引作为键存储数据


# 基于hash的查找
def hash_search(name,file_hash_list,file_index_list):
    with open(file_hash_list, 'rb') as f:
        hash_list = pickle.load(f)
    for lst in hash_list[hash_function(name)]:
        if lst[0] == name:
            with shelve.open(file_index_list) as db:
                return db.get(str(lst[1]), None)  # 通过索引读取数据


# 建立顺序索引表
# def write_index_table_to_csv(file,index_table):
#     data={}
#     names = []
#     index_list = []
#     for name in index_table.keys():
#         names.append(name)
#         index_list.append(index_table[name])
#     data["Token"] = names
#     data["Index"] = index_list
#     df = pd.DataFrame(data)
#     df.to_csv(file,index=False)


book_index_table = csv_to_index_table(file_book_keywords_csv)
book_index_table_sorted = sort_index_table(book_index_table)
book_index_table_skip_builded = skip_list_build(book_index_table_sorted)

movie_index_table = csv_to_index_table(file_movie_keywords_csv)
movie_index_table_sorted = sort_index_table(movie_index_table)
movie_index_table_skip_builded = skip_list_build(movie_index_table_sorted)

index_table_storage(book_index_table_skip_builded,'jieba\data\\book_index_list_with_term')
index_table_storage(movie_index_table_skip_builded,'jieba\data\\movie_index_list_with_term')