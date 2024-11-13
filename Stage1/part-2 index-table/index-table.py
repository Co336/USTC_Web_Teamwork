import pandas as pd

file_book_keywords_csv = "part-2 index-table\\book_keywords.csv"
file_movie_keywords_csv = "part-2 index-table\movie_keywords.csv"

# 建立token索引表
def csv_to_index_table(csvfile):
    index_table = {}
    content = pd.read_csv(csvfile, delimiter=',', header=None, index_col=False)
    idlist = content[0].values
    tokenlist = content[1].values
    for i in range(1,len(idlist)):
        tokens = tokenlist[i].replace("'","").replace("[","").replace("]","").replace(" ","")
        tokens = tokens.split(",")
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

# 建立跳表指针
# 注:此处跳表的结构是建立一个新的列表作为索引,按每跳step个选取原列表元素,查询时同时与多个列表进行比较即可.
#    目前是单层跳表,实际上,多层跳表也只需增加列表的数量即可,但这会使搜索算法复杂度增加,待跳表结构改进后再考虑建立多层跳表.   
def skip_list_build(index_table):
    skip_list = []
    step = 3 
    for key in index_table.keys():
        for i in range(1,len(index_table[key])//step+1):
            skip_list.append(index_table[key][step*i-1])
        index_table[key] = [index_table[key],skip_list]
        skip_list = []
    return index_table

def write_index_table_to_csv(file,index_table):
    data={}
    names = []
    index_list = []
    for name in index_table.keys():
        names.append(name)
        index_list.append(index_table[name])
    data["Token"] = names
    data["Index"] = index_list
    df = pd.DataFrame(data)
    df.to_csv(file,index=False)


book_index_table = csv_to_index_table(file_book_keywords_csv)
book_index_table_sorted = sort_index_table(book_index_table)
book_index_table_skip_builded = skip_list_build(book_index_table_sorted)
write_index_table_to_csv("part-2 index-table\\book_index_table",book_index_table_skip_builded)

movie_index_table = csv_to_index_table(file_movie_keywords_csv)
movie_index_table_sorted = sort_index_table(movie_index_table)
movie_index_table_skip_builded = skip_list_build(movie_index_table_sorted)
write_index_table_to_csv("part-2 index-table\movie_index_table",movie_index_table_skip_builded)