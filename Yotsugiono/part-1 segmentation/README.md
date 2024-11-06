## 数据文件说明

selected_book_top_1200_data_tag.csv : 实验提供的书籍的标签数据集

selected_movie_top_1200_data_tag.csv : 实验提供的电影的标签数据集

hit_stopwords.txt: [哈工大停用词表](https://github.com/goto456/stopwords)

dict_synonym.txt: 手工标注的[同义词表](https://github.com/guotong1988/chinese_dictionary)

jieba-book_keywords.csv：使用jieba分词得到的书籍关键词数据集

jieba-movie_keywords.csv：使用jieba分词得到的电影关键词数据集

## 代码文件说明

jieba-cut.py: 使用jieba分词工具进行分词，根据词典去除停用词及合并同义词。