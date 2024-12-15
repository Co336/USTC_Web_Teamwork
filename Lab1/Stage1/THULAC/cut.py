import thulac
import pandas as pd

file_book_csv = "THULAC\data\selected_book_top_1200_data_tag.csv"
file_movie_csv = "THULAC\data\selected_movie_top_1200_data_tag.csv"
file_stopwords = "THULAC\data\hit_stopwords.txt"
file_synonyms = "THULAC\data\dict_synonym.txt"

def cut_tags_to_keywords(file):
    thu = thulac.thulac(T2S=True,seg_only=True,filt=True)
    content = pd.read_csv(file, delimiter=',', header=None, index_col=False)
    names = content[0].values
    tags = content[1].values
    keywords = {}
    for i in range(1,len(names)):
        tag = tags[i].replace("'","").replace("{","").replace("}","").replace(",","").replace(" ","")
        keyword = [word for word,pos in thu.cut(tag,text=False)]
        keywords[names[i]] = keyword
    return keywords

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
# bk_keywords = delete_stopwords_in_keywords(bk_keywords)
# bk_keywords = merge_synonyms_in_keywords(bk_keywords)

write_keywords_to_csv("THULAC\data\\book_keywords_raw.csv",bk_keywords)

# mv_keywords = cut_tags_to_keywords(file_movie_csv)
# mv_keywords = delete_stopwords_in_keywords(mv_keywords)
# mv_keywords = merge_synonyms_in_keywords(mv_keywords)

# write_keywords_to_csv("THULAC\data\movie_keywords.csv",mv_keywords)

# thu = thulac.thulac(T2S=True,seg_only=True,filt=True)
# keywords= [keyword for keyword,pos in thu.cut("我也不知道怎么办才好,你去找别人吧",text=False)]
    
# print(keywords)
# bk_keywords = merge_synonyms_in_keywords(bk_keywords)
# print(bk_keywords["1046265"])

