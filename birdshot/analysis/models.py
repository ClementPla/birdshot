import torch.nn as nn
import torch
from sklearn.utils.class_weight import compute_class_weight
import numpy as np


class RNN(nn.Module):
    def __init__(self, input_dim, hidden_dim=16, output_dim=1, num_layers=2):
        super(RNN, self).__init__()
        self.rnn = nn.GRU(
            1, hidden_dim, batch_first=True, bidirectional=True, num_layers=num_layers
        )
        self.fc = nn.Linear(hidden_dim * 2, output_dim)

    def forward(self, x):
        out, _ = self.rnn(x)
        B, L, C = out.shape
        out = out.reshape(B * L, C)
        out = self.fc(out)
        out = out.view(B, L, -1)
        return out


def train(
    model,
    xtrain,
    ytrain,
    num_epochs=1000,
    learning_rate=1e-3,
    device=torch.device("cuda"),
    verbose=True,
):
    xtrain = torch.tensor(xtrain, dtype=torch.float32).unsqueeze(2).to(device)
    ytrain = torch.tensor(ytrain, dtype=torch.float32).to(device)
    model = model.to(device)
    class_weight = compute_class_weight(
        class_weight="balanced",
        classes=ytrain.unique().cpu().numpy(),
        y=ytrain.view(-1).cpu().numpy(),
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    class_weight = torch.tensor(class_weight, dtype=torch.float32).to(device)
    loss = nn.CrossEntropyLoss(weight=class_weight)
    for epoch in range(num_epochs):
        model.train()
        optimizer.zero_grad()
        ypred = model(xtrain)
        ypred = ypred.view(-1, 4)
        loss_value = loss(ypred, ytrain.view(-1).long())
        loss_value.backward()
        optimizer.step()

        if epoch % (num_epochs // 10) == 0 and verbose:
            print(f"Epoch {epoch}, Loss: {loss_value.item()}")
    model.eval()
    return model


def load_model():
    model = RNN(input_dim=1, hidden_dim=16, output_dim=4, num_layers=4)

    state_dict = torch.load("models/GRU_4l_16h.pt")
    model.load_state_dict(state_dict)
    model.eval()
    return model


@torch.inference_mode()
def evaluate(model, x, choice="max_proba"):
    if isinstance(x, torch.Tensor):
        if x.ndim == 1:
            x = torch.unsqueeze(x, dim=0)
        if x.ndim == 2:
            x = torch.unsqueeze(x, dim=2)
    else:
        if x.ndim == 1:
            x = np.expand_dims(x, axis=0)

        if x.ndim == 2:
            x = np.expand_dims(x, axis=2)
        x = torch.tensor(x, dtype=torch.float32)
    model.eval()

    with torch.no_grad():
        ypred = model(x)
        yproba = torch.softmax(ypred, dim=-1)
        ypred = yproba.argmax(dim=-1)
    results = {}
    for i, label in enumerate(["i", "b", "a"]):
        i = i + 1

        # Find the largest proba for the i-th class
        if choice == "max_proba":
            idx_max_proba = yproba[:, :, i].argmax(1)
            results[label] = idx_max_proba
        else:
            results[label] = (ypred == i).long().argmax(1)

    return results
