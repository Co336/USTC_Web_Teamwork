import pandas as pd

file_book_csv = "jieba\data\selected_book_top_1200_data_tag.csv"
file_movie_csv = "jieba\data\selected_movie_top_1200_data_tag.csv"
file_stopwords = "jieba\data\hit_stopwords.txt"
file_synonyms = "jieba\data\dict_synonym.txt"

def name_list(file,file2):
    content = pd.read_csv(file, delimiter=',', header=None, index_col=False)
    names = ",".join(content[0].values[1:])
    with open(file2,"w") as f:
        f.write(names)

name_list(file_movie_csv,"moviename.txt")