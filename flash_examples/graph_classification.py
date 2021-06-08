import random

import networkx as nx

import flash
from flash.core.data.data_source import DefaultDataKeys
from flash.core.data.transforms import ApplyToKeys
from flash.core.utilities.imports import _PYTORCH_GEOMETRIC_AVAILABLE
from flash.graph.classification.data import GraphClassificationData
from flash.graph.classification.model import GraphClassifier

if _PYTORCH_GEOMETRIC_AVAILABLE:
    import torch_geometric
    import torch_geometric.transforms as T
    from torch_geometric.data import data as PyGData
    from torch_geometric.datasets import TUDataset
else:
    raise ModuleNotFoundError("Please, pip install -e '.[graph]'")

dataset = TUDataset("data", name='IMDB-BINARY').shuffle()
num_features = 136
transform = {
    "pre_tensor_transform": ApplyToKeys(DefaultDataKeys.INPUT, T.OneHotDegree(num_features - 1)),
    "to_tensor_transform": ApplyToKeys(DefaultDataKeys.INPUT, T.ToSparseTensor())
}
dm = GraphClassificationData.from_datasets(
    train_dataset=dataset[:len(dataset) // 2],
    test_dataset=dataset[len(dataset) // 2:],
    val_split=0.1,
    train_transform=transform,
    val_transform=transform,
    predict_transform=transform,
    num_features=num_features,
)
model = GraphClassifier(num_features=num_features, num_classes=dm.num_classes)

# Alternatively, we may just pass a tuple of one list of torch_geometric.Data objects and another with the labels
dm = GraphClassificationData.from_pygdatasequence(
    train_data=[
        torch_geometric.utils.from_networkx(nx.complete_bipartite_graph(random.randint(1, 10), random.randint(1, 10))),
        torch_geometric.utils.from_networkx(nx.tetrahedral_graph()),
        torch_geometric.utils.from_networkx(nx.complete_bipartite_graph(random.randint(1, 10), random.randint(1, 10))),
    ],
    train_targets=[0, 1, 0]
)
model = GraphClassifier(num_features=1, num_classes=1)

trainer = flash.Trainer(max_epochs=1)
trainer.fit(model, datamodule=dm)

# 7. Save it!
trainer.save_checkpoint("graph_classification.pt")
