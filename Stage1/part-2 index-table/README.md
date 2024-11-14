## 数据文件说明

<!--注：当前所有文件都是在jieba分词,哈工大停用词表,中文同义词表的基础上建立的-->

book_keywords.csv：书籍关键词数据集

movie_keywords.csv：电影关键词数据集

book_index_table.csv: 书籍顺序索引表

movie_index_table.csv: 电影顺序索引表

book_hash_list.pkl：书籍的hash词项存储文件

book_index_list(.bak .dat .dir)：书籍hash对应的索引表文件

book_hash_list.pkl：电影的hash词项存储文件

book_index_list(.bak .dat .dir)：电影hash对应的索引表文件

## 代码文件说明

index-table.py：从原始关键词数据集建立索引表

注：

倒排索引表采用了hash存储方式，词项和索引表分开存储。

词项用pkl文件存储，方便将hash表载入内存，索引表用shelve模块按照键值对存储，方便查找。

在查询时只需将词项hash表载入内存，根据查找词项的hash值查找得到对应词项的索引值，再根据索引值在索引表文件中直接查找即可，避免将较大的索引表载入内存，提高查找效率。