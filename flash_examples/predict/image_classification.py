from flash import Trainer
from flash.core.data import download_data
from flash.vision import ImageClassificationData, ImageClassifier

if __name__ == "__main__":

    # 1. Download the data
    download_data("https://pl-flash-data.s3.amazonaws.com/hymenoptera_data.zip", 'data/')

    # 2. Load the model from a checkpoint
    model = ImageClassifier.load_from_checkpoint("https://flash-weights.s3.amazonaws.com/image_classification_model.pt")

    # 3a. Predict what's on a few images! ants or bees?
    predictions = model.predict([
        "data/hymenoptera_data/val/bees/65038344_52a45d090d.jpg",
        "data/hymenoptera_data/val/bees/590318879_68cf112861.jpg",
        "data/hymenoptera_data/val/ants/540543309_ddbb193ee5.jpg",
    ])
    print(predictions)

    # 3b. Or generate predictions with a whole folder!
    datamodule = ImageClassificationData.from_folder(folder="data/hymenoptera_data/predict/")
    predictions = Trainer().predict(model, datamodule=datamodule)
    print(predictions)
