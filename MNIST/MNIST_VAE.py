import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np


def main():
    
    # Device check
    device = torch.device('cude' if torch.cuda.is_available() else 'cpu')

    # Hyper parameters
    input_size = 784 # 28*28
    hidden_size = 128
    latent_size = 10 # 10 means and 10 variances will be produced in encoder
    num_epochs = 10
    batch_size = 256
    learning_rate = 0.001
    torch.manual_seed(0)

    # MNIST dataset 
    train_dataset = torchvision.datasets.MNIST(root = "./data", train = True, transform=transforms.ToTensor(), download=True)

    n = len(train_dataset)
    train_data, val_data = torch.utils.data.random_split(train_dataset, [int(n-0.2*n), int(0.2*n)])

    test_dataset = torchvision.datasets.MNIST(root="./data", train=False, transform=transforms.ToTensor(), download=True)

    # Loading data
    train_loader = torch.utils.data.DataLoader(dataset=train_data, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(dataset=val_data, batch_size=batch_size)
    test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)

    # Make the Autoencoder
    vae = VariationalAutoEncoder(input_size, hidden_size, latent_size)

    # Make the optimizer
    optim = torch.optim.Adam(vae.parameters(), lr = learning_rate)
    vae.to(device)

    # Training Loop
    for epoch in range(num_epochs):
        train_epoch(vae, device, train_loader, optim, input_size)

    # Displaying some images generated by model
    vae.eval()

    with torch.no_grad():
        noise = torch.randn(128, 10, device=device)
        
        img = vae.decoder(noise)
        img = img.cpu()
        print(img.shape)
        img = img.reshape(-1, 28, 28)
        print(img[0].shape)

        for i in range(100):
            plt.subplot(10, 10, i+1)
            plt.axis('off')
            plt.imshow(img[i], cmap='gray')
        plt.show()




def train_epoch(vae, device, dataloader, optimizer, image_size):
    # Set the train mode (Reason for this is here: https://stackoverflow.com/questions/51433378/what-does-model-train-do-in-pytorch)   
    vae.train()

    # train in one epoch
    for x, _ in dataloader:
        
        # Reshaping x
        x = x.reshape(-1, image_size)

        x = x.to(device)
        x_hat = vae(x)

        # Evaluate loss
        loss = ((x - x_hat)**2).sum() + vae.encoder.kl

        # Backward pass
        optimizer.zero_grad()   # Set all the weights to zero
        loss.backward()         # Compute the gradients wrt the parameters
        optimizer.step()        # Update the new weights




class Encoder(nn.Module):

    def __init__(self, input_features, hidden_size, latent_size) -> None:
        super(Encoder, self).__init__()
        self.l1 = nn.Linear(input_features, hidden_size)
        self.tanh = nn.Tanh()
        self.l2 = nn.Linear(hidden_size, latent_size)    # latent size because we need two tensors for means and variances
        self.l3 = nn.Linear(hidden_size, latent_size)    # second one for the log variances

        self.N = torch.distributions.Normal(0, 1)
        self.kl = 0     # store the forward pass mean and variance divergence over here

    def forward(self, x):
        out = self.l1(x)
        out = self.tanh(out)
        mu = self.l2(out)
        logvar = self.l3(out)
        var = torch.exp(logvar)
        
        ret = mu + var*self.N.sample(mu.shape)

        self.kl = (var**2 + mu**2 - torch.log(var) - 1/2).sum()        

        return ret

class Decoder(nn.Module):
    def __init__(self, latent_size, hidden_size, output_size) -> None:
        super(Decoder, self).__init__()
        self.l1 = nn.Linear(latent_size, hidden_size)
        self.relu = nn.ReLU()
        self.l2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        return out

class VariationalAutoEncoder(nn.Module):

    def __init__(self, image_size, hidden_dims, latent_dims):
        super(VariationalAutoEncoder, self).__init__()
        self.encoder = Encoder(image_size, hidden_dims, latent_dims)
        self.decoder = Decoder(latent_dims, hidden_dims, image_size)

    def forward(self, x):
        x = self.encoder(x)
        return self.decoder(x)

if __name__ == "__main__":
    main()
