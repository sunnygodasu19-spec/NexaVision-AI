"""Train a small transfer-learning classifier from a folder dataset.

Expected folders:
dataset/
  real/  (real photographs)
  ai/    (AI-generated images)

Example:
python train.py --data dataset --epochs 5

This starter training script is educational. Model quality depends heavily on
dataset quality, balance, diversity, and evaluation methodology.
"""
import argparse
from pathlib import Path
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="dataset", help="Folder with real/ and ai/ subfolders")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    import tensorflow as tf
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    data_dir = Path(args.data)
    if not (data_dir / "real").is_dir() or not (data_dir / "ai").is_dir():
        raise SystemExit(
            f"Dataset folders not found in {data_dir}. Expected {data_dir}/real and {data_dir}/ai. "
            "See README.md for setup instructions."
        )

    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training", seed=42,
        image_size=(224, 224), batch_size=args.batch_size,
        label_mode="binary", class_names=["real", "ai"]
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation", seed=42,
        image_size=(224, 224), batch_size=args.batch_size,
        label_mode="binary", class_names=["real", "ai"]
    )
    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.map(lambda x, y: (preprocess_input(x), y)).prefetch(autotune)
    val_ds = val_ds.map(lambda x, y: (preprocess_input(x), y)).prefetch(autotune)

    backbone = MobileNetV2(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
    backbone.trainable = False
    inputs = layers.Input(shape=(224, 224, 3))
    x = backbone(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)
    model = Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss="binary_crossentropy", metrics=["accuracy", tf.keras.metrics.AUC(name="auc")])
    history = model.fit(train_ds, validation_data=val_ds, epochs=args.epochs)
    out_dir = Path("models")
    out_dir.mkdir(exist_ok=True)
    model.save(out_dir / "fake_image_detector.keras")
    metrics = {key: [float(v) for v in values] for key, values in history.history.items()}
    (out_dir / "evaluation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved model to {out_dir / 'fake_image_detector.keras'}")
    print("Note: validate on a separate, diverse test set before interpreting model scores.")


if __name__ == "__main__":
    main()
