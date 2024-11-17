import pandas as pd
import re
import time
import shelve

file_book_index_table_csv = "jieba\data\\book_index_table.csv"
file_movie_index_table_csv = "jieba\data\movie_index_table.csv"

def csv_to_dict(csvfile):
    dict = {}
    content = pd.read_csv(csvfile, delimiter=',', header=None, index_col=False)
    keys = content[0].values
    values = content[1].values
    for i in range(1,len(keys)):
        dict[keys[i]] = eval(values[i])
    return dict

def get_all_name(txtfile):
    with open(txtfile) as f:
        namelist = f.read().split(",")
    namelist.sort()
    return namelist


# 跳表索引映射规则,这里默认每跳为3
def skip_index(key):
    return 3*(key+1)-1

# bool查询函数
def merge_AND(list_key_a, list_key_b):
    And_list = []
    # 确定待合并列表大小关系,小的列表在大的列表上找以获得更多跳表机会
    if(len(list_key_a[0])>len(list_key_b[0])):
        # 大列表需保留跳表索引以便查询,小列表则不需要
        search_list = list_key_a
        base_list = list_key_b[0]
    else:
        search_list = list_key_b
        base_list = list_key_a[0]
    # 合并操作
    j = k = 0 # 初始化两个顺序变量(搜索列表和其跳表索引列表)
    for i in range(len(base_list)):
        current_id = base_list[i]
        while j < len(search_list[0]):
            # 先在跳表索引上比较
            if k < len(search_list[1]):
                skip_id = search_list[1][k]
                if current_id >= skip_id:
                    j = skip_index(k)
                    k+=1
                    continue
            # 找到合适区间后再在搜索列表中查找
            compare_id = search_list[0][j]
            if current_id > compare_id:
                j+=1
                continue
            elif current_id == compare_id:
                And_list.append(current_id)
                break
            else:
                break
    # 合并列表后在此基础上建立跳表
    skip_list = []
    step = 3 
    for i in range(1,len(And_list)//step+1):
        skip_list.append(And_list[step*i-1])
    And_list = [And_list,skip_list]
    return And_list

def merge_OR(list_key_a, list_key_b):
    OR_list = []
    # 确定待合并列表大小关系,小的列表在大的列表上找以获得更多跳表机会
    if(len(list_key_a[0])>len(list_key_b[0])):
        # 大列表需保留跳表索引以便查询,小列表则不需要
        search_list = list_key_a
        base_list = list_key_b[0]
    else:
        search_list = list_key_b
        base_list = list_key_a[0]
    # 合并操作
    OR_list = search_list[0].copy()
    j = k = 0 # 初始化两个顺序变量(搜索列表和其跳表索引列表)
    for i in range(len(base_list)):
        current_id = base_list[i]
        while j < len(search_list[0]):
            # 先在跳表索引上比较
            if k < len(search_list[1]):
                skip_id = search_list[1][k]
                if current_id >= skip_id:
                    j = skip_index(k)
                    k+=1
                    continue
            # 找到合适区间后再在搜索列表中查找
            compare_id = search_list[0][j]
            if current_id > compare_id:
                j+=1
                continue
            elif current_id == compare_id:
                break
            else:
                OR_list.insert(j,current_id)
                break
    # 合并列表后在此基础上建立跳表
    skip_list = []
    step = 3 
    for i in range(1,len(OR_list)//step+1):
        skip_list.append(OR_list[step*i-1])
    OR_list = [OR_list,skip_list]
    return OR_list

def search_NOT(list_key_a,all_docs):
    not_list = all_docs.copy()
    for i in list_key_a[0]:
        not_list.remove(i)
    return not_list

def merge_ANDNOT(list_key_a, list_key_b):
    ANDNOT_list = []
    search_list = list_key_a
    base_list = list_key_b[0]
    # 合并操作
    ANDNOT_list = search_list[0].copy()
    j = k = 0 # 初始化两个顺序变量(搜索列表和其跳表索引列表)
    for i in range(len(base_list)):
        current_id = base_list[i]
        while j < len(search_list[0]):
            # 先在跳表索引上比较
            if k < len(search_list[1]):
                skip_id = search_list[1][k]
                if current_id >= skip_id:
                    j = skip_index(k)
                    k+=1
                    continue
            # 找到合适区间后再在搜索列表中查找
            compare_id = search_list[0][j]
            if current_id > compare_id:
                j+=1
                continue
            elif current_id == compare_id:
                ANDNOT_list.remove(current_id)
                break
            else:
                break
    # 合并列表后在此基础上建立跳表
    skip_list = []
    step = 3 
    for i in range(1,len(ANDNOT_list)//step+1):
        skip_list.append(ANDNOT_list[step*i-1])
    ANDNOT_list = [ANDNOT_list,skip_list]
    return ANDNOT_list

# 查询解析器类
class BooleanQueryParser:
    def __init__(self, inverted_index, all_docs):
        self.index = inverted_index
        self.docs = all_docs

    def evaluate(self, query):
        tokens = self.tokenize(query)
        return self.parse(tokens)

    def tokenize(self, query):
        # 使用正则表达式分割查询字符串为tokens
        tokens = re.findall(r'\w+|[()!&|]', query)
        return tokens

    def parse(self, tokens):
        # 递归下降解析器
        def parse_expr(tokens):
            term = parse_term(tokens)
            while tokens and tokens[0] in ('OR'):
                operator = tokens.pop(0)
                right = parse_term(tokens)
                term = merge_OR(term, right) if operator == 'OR' else term
            return term

        def parse_term(tokens):
            factor = parse_factor(tokens)
            while tokens and tokens[0] in ('AND', 'ANDNOT'):
                operator = tokens.pop(0)
                right = parse_factor(tokens)
                if operator == 'AND':
                    factor = merge_AND(factor, right)
                elif operator == 'ANDNOT':
                    factor = merge_ANDNOT(factor, right)
            return factor

        def parse_factor(tokens):
            if not tokens:
                raise ValueError("Unexpected end of input")
            
            token = tokens.pop(0)
            
            if token == '(':
                # 处理括号内的表达式
                expr = parse_expr(tokens)
                if not tokens or tokens.pop(0) != ')':
                    raise ValueError("Expected closing parenthesis")
                return expr
            elif token == '!':
                # 处理 NOT 操作
                operand = parse_factor(tokens)
                return search_NOT(operand,self.docs)
            else:
                with shelve.open(self.index) as db:
                    return db.get(str(token), [[],[]])  # 通过索引读取数据
                # 不存在时返回空列表
                return [[],[]]
        
        return parse_expr(tokens)

def Book_bool_query():
    # 获取倒排索引表
    file_inverted_index = 'jieba\data\\book_index_list_with_term'
    # 获取所有文档id
    all_docs = get_all_name("jieba\data\\bookname.txt")
    # 创建一个查询解析器并执行查询
    parser = BooleanQueryParser(file_inverted_index,all_docs)
    query = input("Please enter your query:\n")
    start = time.time()
    result = parser.evaluate(query)[0]
    end = time.time()
    print(f"Query result:\n {result}")
    print(f"Search time: {end-start}")

def Movie_bool_query():
    # 获取倒排索引表
    file_inverted_index = 'jieba\data\\movie_index_list_with_term'
    # 获取所有文档id
    all_docs = get_all_name("jieba\data\\moviename.txt")
    # 创建一个查询解析器并执行查询
    parser = BooleanQueryParser(file_inverted_index,all_docs)
    query = input("Please enter your query:\n")
    start = time.time()
    result = parser.evaluate(query)[0]
    end = time.time()
    print(f"Query result:\n {result}")
    print(f"Search time: {end-start}")

Book_bool_query()
Book_bool_query()
Movie_bool_query()