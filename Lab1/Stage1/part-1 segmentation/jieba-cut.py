import jieba
import pandas as pd

file_book_csv = "selected_book_top_1200_data_tag.csv"
file_movie_csv = "selected_movie_top_1200_data_tag.csv"
file_stopwords = "hit_stopwords.txt"    #哈工大停用词表
file_synonyms = "dict_synonym.txt"      #同义词表

# 将tags提取出来并进行分词操作
def cut_tags_to_keywords(file):
    content = pd.read_csv(file, delimiter=',', header=None, index_col=False)
    names = content[0].values
    tags = content[1].values
    keywords = {}
    for i in range(1,len(names)):
        tag = tags[i].replace("'","").replace("{","").replace("}","").replace(",","").replace(" ","")
        keyword = list(jieba.cut_for_search(tag))
        keywords[names[i]] = keyword
    return keywords

# 根据停用词表删除keywords中的停用词
def delete_stopwords_in_keywords(keywords):
    stopwords = []
    with open(file_stopwords, 'r', encoding='utf-8') as file:
        for line in file:
            stopwords.append(line.strip())
    for kwords in list(keywords.values()):
        for kword in kwords:
            if kword in stopwords:
                kwords.remove(kword)
    return keywords

# 根据同义词表将keywords中的同义词归一化(统一为表中第一个词)
def merge_synonyms_in_keywords(keywords):
    synonyms = []
    with open(file_synonyms, 'r', encoding='utf-8') as file:
        for line in file:
            if '=' in line:
                synonyms.append(line[9:].split())
    for kwords in list(keywords.values()):
        for i in range(len(kwords)):
            for synonym in synonyms:
                if kwords[i] in synonym:
                    kwords[i] = synonym[0]

    return keywords

# 将处理完毕的keywords写入文件
def write_keywords_to_csv(file,keywords):
    data={}
    names = []
    kwords = []
    for name in keywords.keys():
        names.append(name)
        kwords.append(keywords[name])
    data["Name"] = names
    data["Keywords"] = kwords
    df = pd.DataFrame(data)
    df.to_csv(file,index=False)
    

bk_keywords = cut_tags_to_keywords(file_book_csv)
bk_keywords = delete_stopwords_in_keywords(bk_keywords)
bk_keywords = merge_synonyms_in_keywords(bk_keywords)

write_keywords_to_csv("jieba-book_keywords.csv",bk_keywords)

mv_keywords = cut_tags_to_keywords(file_movie_csv)
mv_keywords = delete_stopwords_in_keywords(mv_keywords)
mv_keywords = merge_synonyms_in_keywords(mv_keywords)

write_keywords_to_csv("jieba-movie_keywords.csv",mv_keywords)




