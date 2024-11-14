## 数据文件说明

<!--注：当前所有文件都是在jieba分词,哈工大停用词表,中文同义词表的基础上建立的-->

book_index_table.csv：书籍顺序索引表

movie_index_table.csv：电影顺序索引表

bookname.txt：书籍文档名全列表

moviename.txt：电影文档名全列表

book_hash_list.pkl：书籍的hash词项存储文件

book_index_list(.bak .dat .dir)：书籍hash对应的索引表文件

book_hash_list.pkl：电影的hash词项存储文件

book_index_list(.bak .dat .dir)：电影hash对应的索引表文件

## 代码文件说明

bool-query.py：基于顺序索引文件的布尔查询

bool-query with hash.py：基于hash存储索引文件的布尔查询