
import gensim
import numpy as np
from scipy.spatial.distance import pdist
from textprocess.textcut import *
from semdistance.model_path import *

# get vector model
def get_model(model_path):
    model = gensim.models.KeyedVectors.load_word2vec_format(os.path.join(model_path), binary=True)
    return model

# word vector model
model_test = get_model(model_test_path)
model_trained = get_model(model_trained_path)

# get word vector
def get_word_vector(word,have_model):
    if have_model == 0:
        model = model_test
    else:
        model = model_trained
    try:
        return model[word]
    except:
        try:
            word_list = textcut(word)
            vector_list = [model[w] for w in word_list]
            return np.mean(vector_list,0)

        except:
            print(word)
            print('该词语在词典中未检测到！')
            return np.zeros(300)[: int(300)]
            # return 

# unit vector calculation
def _unitvec(v): return v/ np.linalg.norm(v)

# get word sequence vector
def get_word_sequence_vector(word_sequence,model=0):
    vector_list = []
    for word in word_sequence:
        v = get_word_vector(word, model)
        if not(np.all(v==0)):
            vector_list.append(v)
    return vector_list

# distance calculation between words
def dis_words(word1, word2, model=0,size=300):
    return 1 - np.dot(_unitvec(get_word_vector(word1,model)),
                  _unitvec(get_word_vector(word2,model)))

# Euclidean distance
def dis_Euclidean_words(word1, word2, model=0,size=300):
    vec1 = get_word_vector(word1,model)
    vec2 = get_word_vector(word2,model)
    vec = np.vstack([vec1,vec2])
    # sk = np.var(vec,axis=0,ddof=1)
    # distance = np.sqrt(((vec1-vec2)**2 / sk).sum())
    distance = pdist(vec, 'seuclidean')
    return distance[0]
                   
def dis_Euclidean_words_by_vector(vec1,vec2):
    return pdist(np.vstack([vec1,vec2]), 'seuclidean')[0]

def dis_words_by_vec(vec1,vec2):
    return 1 - np.dot(_unitvec(vec1),_unitvec(vec2))

# forward flow distance calculation
def dis_FFT(word_sequence,model=0):
    vector_list = get_word_sequence_vector(word_sequence,model)
    dis_j_mean = []
    for j in range(1,len(vector_list)):
        dis_j = []
        for i in range(j):
            dis_j.append(dis_words_by_vec(vector_list[j],vector_list[i]))
        dis_j_mean.append(np.mean(dis_j,0))
    distance = np.mean(dis_j_mean,0)
    return distance

# Adjacent words distance calculation
def dis_ajac(word_sequence,model=0):
    vector_list = get_word_sequence_vector(word_sequence,model)
    dis_i_j = []
    for j in range(len(vector_list)-1):
        dis_i_j.append(dis_words_by_vec(vector_list[j], vector_list[j+1]))
    distance = np.mean(dis_i_j,0)    
    return distance

# first last words distance calculation
def dis_firstlast(word_sequence,model=0):
    vector_list = get_word_sequence_vector(word_sequence,model)
    return dis_words_by_vec(vector_list[0],vector_list[-1])


# get relation vector by subtracting word vectors from word pairs  
def get_relation_vector(pair,model=0):
        vec1,vec2 = [get_word_vector(p,model_path) for p in pair]
        relation_vector = np.subtract(word1,word2)
        return relation_vector

# semantic relation distance
def dis_pairs(pair1,pair2,model=0):
    return 1 - np.dot(_unitvec(get_relation_vector(pair1,model)), _unitvec(get_sentence_vector(pair2,model)))


# get sentence vector by averaging word vector in the sentence
def get_sentence_vector(s, model=0):
    vectorized_sentence = [get_word_vector(w,model) for w in textcut(s)]
    sentence_vector = np.mean(vectorized_sentence, 0)
    return sentence_vector


# distance calculation between sentences
def dis_sentences(s1, s2, model=0):
    return 1 - np.dot(_unitvec(get_sentence_vector(s1,model)), _unitvec(get_sentence_vector(s2,model)))

# distance calculatioin in text 
def mean_distances(vectors, vec_len):
    dists = []
    for i in range(vec_len - 1):
        for j in range(i+1,vec_len):
            dists.append(1 - np.dot(_unitvec(vectors[i]), _unitvec(vectors[j])))
    mean_distance = np.mean(dists)

    return mean_distance


# word-based text mean semantic distance calculation
def word_based_text_distance(text, model=0):
    words = textcut(text)
    wc = len(words)  # 词语个数
    vecs_word = [get_word_vector(w,model) for w in words]
    distance = mean_distances(vecs_word, wc)  # 文章平均语义距离

    return distance

# sentence-based text mean semantic distance calculation(sentence no overlap)
def sentence_based_text_distance_no_window(text, wind, model=0):
    wcut = textcut(text)  # 分词
    # k = 5 #i的步长
    wc = len(wcut)  # 词语数
    left = wc % wind  # 余数
    # m = int(l / wind) * wind-k
    m = wc - left  # 最后一个句子的索引值
    vec_sents = []  # 每个句子的向量
    for i in range(0, m, wind):
        if (i != m):
            vec_sents.append(np.mean([get_word_vector(w,model) for w in wcut[i:i + wind]], 0))
        else:
            vec_sents.append(np.mean([get_word_vector(w,model) for w in wcut[i:]], 0))
    distance = mean_distances(vec_sents, len(vec_sents))  # 平均语义距离
    return distance


# 计算全局语义距离，即文章的平均语义距离，滑动窗口，句子间有重叠，k为滑动距离
# sentence-based text mean semantic distance calculation(sentence overlap)
def sentence_based_text_distance_by_window(text, wind, k, model=0):
    words_cut = textcut(text)  # 分词
    wc = len(words_cut)
    # k = 10  # i的步长
    # c = int(words_len/wind)*wind-b
    c = int((wc - wind) / k) * k  # 最后一个句子的索引值
    vectors_sent = []
    # 所有句子窗口向量
    for i in range(0, c + 1, k):
        if (i != c):
            vectors_sent.append(np.mean([get_word_vector(w,model) for w in words_cut[i:i + wind]], 0))
        else:
            vectors_sent.append(np.mean([get_word_vector(w,model) for w in words_cut[i:]], 0))
    # vectors_sent = [np.mean([get_vector(w) for w in words_cut[i:i + wind]],0) for i in range(0,c,b)]

    sent_len = len(vectors_sent)  # 句子向量的个数
    global_dist = mean_distances(vectors_sent, sent_len)
    
    return global_dist


def text_distance(text,model=0,wind=0,k=0):
    if wind == 0:
        word_based_text_distance(text,model)
    else:
        if k == 0:
            sentence_based_text_distance_no_window(text,model,wind)
        else:
            sentence_based_text_distance_by_window(text,model, wind, k)
    
    
