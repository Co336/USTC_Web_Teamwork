def load_movie_id_map(movie_id_map_file):
    """加载电影实体ID映射关系"""
    movie_id_map0 = {}
    movie_id_map = {}
    with open(movie_id_map_file, 'r', encoding='utf-8') as f,open(movie_id_map_file2, 'r', encoding='utf-8') as g:
        for line in f:
            movie_id, movie_index = line.strip().split('\t')
            movie_id_map0[movie_id] = int(movie_index)
        for line in g:
            movie_id, dbmovie_id = line.strip().split('\t')
            movie_id_map[dbmovie_id] = movie_id_map0[movie_id]
    return movie_id_map

def load_graph_data(graph_data_file):
    """加载图谱数据,每行是三元组:头实体ID, 关系ID, 尾实体ID"""
    triples = []
    with open(graph_data_file, 'r', encoding='utf-8') as f:
        for line in f:
            head, relation, tail = line.strip().split('\t')
            triples.append((head, relation, tail))
    return triples

def map_entities_and_relations(movie_id_map, triples):
    """将实体和关系映射到指定的范围内"""
    entity_map = {}  # 存储实体ID到索引的映射
    relation_map = {}  # 存储关系ID到索引的映射

    num_movies = len(movie_id_map)
    num_entities = num_movies  # 初始化实体的范围为电影数
    num_relations = 0  # 初始化关系的范围

    # 第一步：映射电影实体ID
    for movie_id in movie_id_map:
        entity_map[movie_id] = movie_id_map[movie_id]

    # 第二步：映射其他实体
    for head, relation, tail in triples:
        # 映射头实体
        if head not in movie_id_map:
            if head not in entity_map:
                entity_map[head] = num_entities
                num_entities += 1
        # 映射尾实体
        if tail not in movie_id_map:
            if tail not in entity_map:
                entity_map[tail] = num_entities
                num_entities += 1
        # 映射关系
        if relation not in relation_map:
            relation_map[relation] = num_relations
            num_relations += 1

    return entity_map, relation_map, num_entities, num_relations

def convert_to_indexed_triples(triples, entity_map, relation_map):
    """将实体和关系映射到索引值，返回三元组"""
    indexed_triples = []
    for head, relation, tail in triples:
        head_index = entity_map.get(head)
        relation_index = relation_map.get(relation)
        tail_index = entity_map.get(tail)
        if head_index is not None and relation_index is not None and tail_index is not None:
            indexed_triples.append((head_index, relation_index, tail_index))
    return indexed_triples

def save_indexed_triples(indexed_triples, output_file):
    """将映射后的三元组保存到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for head_index, relation_index, tail_index in indexed_triples:
            f.write(f"{head_index} {relation_index} {tail_index}\n")

def main(movie_id_map_file, graph_data_file, output_file):
    """主函数，执行整个映射过程"""
    # 1. 加载电影实体ID映射
    movie_id_map = load_movie_id_map(movie_id_map_file)
    # 2. 加载图谱数据
    triples = load_graph_data(graph_data_file)
    # 3. 映射实体和关系
    entity_map, relation_map, num_entities, num_relations = map_entities_and_relations(movie_id_map, triples)
    # 4. 转换为索引后的三元组
    indexed_triples = convert_to_indexed_triples(triples, entity_map, relation_map)
    # 5. 保存映射后的三元组
    save_indexed_triples(indexed_triples, output_file)
    print(f"已将映射后的三元组保存到 {output_file}")

if __name__ == "__main__":
    movie_id_map_file = 'lab2/movie_id_map.txt'  # 电影ID映射文件路径
    movie_id_map_file2 = 'lab2/douban2fb.txt'  # 电影ID映射文件路径
    graph_data_file = 'lab2/matched_triples.txt'  # 图谱数据文件路径
    output_file = 'lab2/kg_final.txt'  # 输出文件路径

    main(movie_id_map_file, graph_data_file, output_file)
