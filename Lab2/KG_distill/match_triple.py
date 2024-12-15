import gzip
import io
import multiprocessing as mp
from tqdm import tqdm
from itertools import islice

# 前缀,筛选出符合条件的三元组
FB_PREFIX = '<http://rdf.freebase.com/ns/'

# 获取所有可匹配的Freebase ID
def load_mapfreebase_id(file='lab2\douban2fb.txt'):
    fb_ids = []
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            fb_ids.append(line.strip().split('\t')[1])
    return fb_ids

# 预处理数据块
def process_chunk(args):
    chunk, matched_fb_entities = args
    local_triples = []
    
    for line in chunk:
        try:
            line = line.strip()
            if line.endswith(' .'):
                line = line[:-2]
            elif line.endswith('.'):
                line = line[:-1]
            parts = [p for p in line.split() if p]
            if len(parts) != 3:
                continue
            
            head, relation, tail = parts
            # 检查头尾实体是否都具有正确的前缀
            if not (head.startswith(FB_PREFIX) and tail.startswith(FB_PREFIX)):
                continue
            
            # 提取出fb id
            head = head[1:-1].split('/')[-1] if head.startswith('<') else head
            tail = tail[1:-1].split('/')[-1] if tail.startswith('<') else tail
            
            # 将匹配的三元组加入三元组数组
            if head in matched_fb_entities:
                local_triples.append((head, relation[1:-1] if relation.startswith('<') else relation, tail))
            elif tail in matched_fb_entities:
                local_triples.append((head, relation[1:-1] if relation.startswith('<') else relation, tail))
        except Exception as e:
            continue
            
    return local_triples

# 提取三元组中匹配的实体信息
def extract_matched_entities():
    douban_to_fb = load_mapfreebase_id()
    matched_fb_entities = set(douban_to_fb)
    
    num_processes = mp.cpu_count()
    chunk_size = 10000  # 减小每个块的大小
    
    matched_triples = []
    total_triples = 0
    
    BUFFER_SIZE = 1024 * 1024 * 32
    
    with gzip.open('lab2\\freebase_douban.gz', 'rb') as gz_file:
        with io.BufferedReader(gz_file, buffer_size=BUFFER_SIZE) as buf_reader:
            with io.TextIOWrapper(buf_reader, encoding='utf-8') as f:
                with mp.Pool(num_processes) as pool:
                    pbar = tqdm(total=52 * 1024 * 1024 * 1024, unit='B', unit_scale=True)
                    
                    # 读取多个数据块
                    chunks = []
                    chunk_bytes = 0
                    
                    while True:
                        chunk = list(islice(f, chunk_size))
                        if not chunk:
                            break
                            
                        chunks.append(chunk)
                        chunk_bytes += sum(len(line.encode('utf-8')) for line in chunk)
                        
                        # 当累积了足够多的块时，并行处理它们
                        if len(chunks) >= num_processes * 2:  # 保持进程池忙碌
                            # 并行处理所有块
                            chunk_args = [(c, matched_fb_entities) for c in chunks]
                            results = pool.map(process_chunk, chunk_args)
                            
                            # 收集结果
                            for result in results:
                                matched_triples.extend(result)
                                total_triples += len(result)
                            
                            # 更新进度条
                            pbar.update(chunk_bytes)
                            chunk_bytes = 0
                            
                            # 清空块列表
                            chunks = []
                            
                            # 定期保存结果
                            if total_triples > 0 and total_triples % 100000 == 0:
                                save_partial_results(matched_triples, total_triples)
                                print(f"\n当前已找到 {total_triples} 个匹配的三元组")
                    
                    # 处理剩余的块
                    if chunks:
                        chunk_args = [(c, matched_fb_entities) for c in chunks]
                        results = pool.map(process_chunk, chunk_args)
                        for result in results:
                            matched_triples.extend(result)
                            total_triples += len(result)
                        pbar.update(chunk_bytes)
                    
                    pbar.close()
    
    print(f"提取了 {len(matched_triples)} 个相关三元组")
    return matched_triples

# 保存部分结果到文件
def save_partial_results(triples, count):
    with open(f'lab2\\matched_triples_{count}.txt', 'w', encoding='utf-8') as f:
        for head, relation, tail in triples:
            f.write(f"{head}\t{relation}\t{tail}\n")

def main():
    matched_triples = extract_matched_entities()
    
    if matched_triples:
        with open('lab2\\matched_triples.txt', 'w', encoding='utf-8') as f:
            for head, relation, tail in matched_triples:
                f.write(f"{head}\t{relation}\t{tail}\n")
        print("处理完成，结果已保存到 matched_triples.txt")
    else:
        print("没有匹配的三元组")
            


if __name__ == "__main__":
    main()
