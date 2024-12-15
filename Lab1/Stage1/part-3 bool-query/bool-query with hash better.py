import pandas as pd
import pickle
import shelve
import re
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

# 将hash表载入内存
def hash_load(file_hash_list):
    with open(file_hash_list, 'rb') as f:
        hash_list = pickle.load(f)
    return hash_list

#
def hash_search(word,hash_list,file_index_list):
    for lst in hash_list[hash_function(word)]:
        if lst[0] == word:
            with shelve.open(file_index_list) as db:
                return db.get(str(lst[1]), None)  # 通过索引读取数据
    return [[],[]]

def get_all_name(txtfile):
    with open(txtfile) as f:
        namelist = f.read().split(",")
    namelist.sort()
    return namelist


# 跳表索引映射规则,这里每跳为根号L
def skip_index(key,len):
    return math.floor(math.sqrt(len))*(key+1)-1

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
                    j = skip_index(k,len(search_list[0]))
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
    # 合并列表后在此基础上建立跳表，确定合并词项文档频率
    skip_list = []
    if And_list:
        step = math.floor(math.sqrt(len(And_list))) 
        for i in range(1,len(And_list)//step+1):
            skip_list.append(And_list[step*i-1])
    And_list = [And_list,skip_list,len(And_list)]
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
                    j = skip_index(k,len(search_list[0]))
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
    # 合并列表后在此基础上建立跳表，确定合并词项文档频率
    skip_list = []
    if OR_list:
        step = math.floor(math.sqrt(len(OR_list))) 
        for i in range(1,len(OR_list)//step+1):
            skip_list.append(OR_list[step*i-1])
    OR_list = [OR_list,skip_list,len(OR_list)]
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
                    j = skip_index(k,len(search_list[0]))
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
    # 合并列表后在此基础上建立跳表，确定合并词项文档频率
    skip_list = []
    if ANDNOT_list:
        step = math.floor(math.sqrt(len(ANDNOT_list))) 
        for i in range(1,len(ANDNOT_list)//step+1):
            skip_list.append(ANDNOT_list[step*i-1])
    ANDNOT_list = [ANDNOT_list,skip_list,len(ANDNOT_list)]
    return ANDNOT_list

# 查询解析器类
class BooleanQueryParser:
    def __init__(self,hash_list , file_inverted_index, all_docs):
        self.hash = hash_list
        self.index = file_inverted_index
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
            factors = [parse_factor(tokens)]
            while tokens and tokens[0] in ('AND', 'ANDNOT'):
                operator = tokens.pop(0)
                right = parse_factor(tokens)
                if operator == 'AND':
                    factors.append(right)
                elif operator == 'ANDNOT':
                    factors.append(('ANDNOT', right))
            # 处理AND操作优先于ANDNOT操作
            return self.process_and_operations(factors)

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
                # 查找倒排索引中存在的token
                return hash_search(token,self.hash,self.index)
        
        return parse_expr(tokens)
    
    def get_factor_frequency(self, factor):
        if isinstance(factor, tuple) and factor[0] == 'ANDNOT':
            return factor[1][0]
        elif isinstance(factor, list):
            return len(factor[0])

    # 处理AND和ANDNOT操作
    def process_and_operations(self, factors):
        and_factors = [factor for factor in factors if isinstance(factor, list)]
        and_not_factors = [factor for factor in factors if isinstance(factor, tuple) and factor[0] == 'ANDNOT']

        # 先处理AND操作
        if len(and_factors) > 1:
            and_factors = sorted(and_factors, key=lambda x: len(x[0]))  # 按频度升序排列
            result = and_factors[0]
            for factor in and_factors[1:]:
                result = merge_AND(result, factor)
        else:
            result = and_factors[0] if and_factors else [[],[]]

        # 合并ANDNOT后的词项，通过OR合并后再执行ANDNOT操作
        if and_not_factors:
            # 先对所有ANDNOT后的因子执行OR操作
            or_result = [[],[]]
            for and_not in and_not_factors:
                or_result = merge_OR(or_result, and_not[1])
            # 执行最终的ANDNOT操作
            result = merge_ANDNOT(result, or_result)

        return result

def Book_bool_query():
    # 载入hash表
    hashlist = hash_load('part-3 bool-query\\book_hash_list.pkl')
    # 获取倒排索引表文件
    file_inverted_index = 'part-3 bool-query\\book_index_list'
    # 获取所有文档id
    all_docs = get_all_name("part-3 bool-query\\bookname.txt")
    # 创建一个查询解析器并执行查询
    parser = BooleanQueryParser(hashlist,file_inverted_index,all_docs)
    query = input("Please enter your query:\n")
    result = parser.evaluate(query)[0]
    print(f"Query result:\n {result}")

def Movie_bool_query():
    # 载入hash表
    hashlist = hash_load('part-3 bool-query\\movie_hash_list.pkl')
    # 获取倒排索引表文件
    file_inverted_index = 'part-3 bool-query\\movie_index_list'
    # 获取所有文档id
    all_docs = get_all_name("part-3 bool-query\\moviename.txt")
    # 创建一个查询解析器并执行查询
    parser = BooleanQueryParser(hashlist,file_inverted_index,all_docs)
    query = input("Please enter your query:\n")
    result = parser.evaluate(query)[0]
    print(f"Query result:\n {result}")


Book_bool_query()
# Movie_bool_query()