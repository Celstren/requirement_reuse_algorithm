from sklearn import metrics
from sklearn.cluster import Birch
from utils import tokenize

from gensim.models.doc2vec import Doc2Vec

def cluster_requirements(model_path, requirements, n_clusters):
    """
    Cluster requirements given
    :param model_path:
    :param feature_path:
    :return:
    """
    features = tokenize(requirements)

    # load model
    model = Doc2Vec.load(model_path)
    # test_docs = [x.strip().split() for x in codecs.open(test_docs, "r", "utf-8").readlines()]

    X = []
    for d in features:
        X.append(model.infer_vector(d))
        # X.append(m.infer_vector(d, alpha=start_alpha, steps=infer_epoch))

    brc = Birch(branching_factor=50, n_clusters=n_clusters, threshold=0.05, compute_labels=True)
    brc.fit(X)

    clusters = brc.predict(X)

    # labels = brc.labels_
    #
    # print("Clusters: ")
    # print(clusters)

    # silhouette_score = metrics.silhouette_score(X, labels, metric='euclidean')

    # print("Silhouette_score: ")
    # print(silhouette_score)

    # return clusters, silhouette_score
    return clusters