import tensorflow as tf
import os
import pandas as pd
from pprint import pprint

import logging
from logging import info, error
from sklearn.preprocessing import MinMaxScaler


# Strictly for testing
def main():
    feature_fields: list = [
        "PRESSURE_REDUCED_TO_MSL_PASCAL",
        "VISIBILITY_AT_SURFACE_METERS",
        "VISIBILITY_AT_CLOUD_TOP_METERS",
        "WIND_GUST_SPEED_AT_SURFACE_METERS_PER_SEC",
        "PRESSURE_AT_SURFACE_PASCAL",
        "TEMPERATURE_AT_SURFACE_KELVIN",
        "DEWPOINT_TEMPERATURE_2_METERS_ABOVE_SURFACE_KELVIN",
        "RELATIVE_HUMIDITY_2_METERS_ABOVE_SURFACE_PERCENT",
        "ALBEDO_PERCENT",
        "TOTAL_CLOUD_COVER_PERCENT"
    ]
    label_field: str = "SOIL_TEMPERATURE_0_TO_01_M_BELOW_SURFACE_KELVIN"
    epochs: int = 5
    learning_rate: float = 0.01
    normalize_inputs: bool = True
    train_split: float = 0.8
    test_split: float = 0.2
    optimizer = tf.keras.optimizers.Adam(learning_rate)
    loss = "mean_squared_error"
    gis_join: str = "G1300490"

    # Load data
    csv_path: str = f"/tmp/model_service/{gis_join}.csv"
    all_df: pd.DataFrame = pd.read_csv(csv_path, header=0).drop("GISJOIN", 1)
    if normalize_inputs:
        scaled = MinMaxScaler(feature_range=(0, 1)).fit_transform(all_df)
        all_df = pd.DataFrame(scaled, columns=all_df.columns)

    features = all_df[feature_fields]
    labels = all_df[label_field]

    # Create Sequential model
    model = tf.keras.Sequential()

    # Add input layer
    model.add(tf.keras.Input(shape=(len(feature_fields))))

    # Add hidden layers
    model.add(tf.keras.layers.Dense(units=32, activation="relu", name="hl_1"))
    model.add(tf.keras.layers.Dense(units=16, activation="relu", name="hl_2"))

    # Add output layer
    model.add(tf.keras.layers.Dense(units=1, activation="relu", name="output_layer"))

    # Compile the model and print its summary
    model.compile(loss=loss, optimizer=optimizer)
    model.summary()

    # Fit the model to the data
    history = model.fit(features, labels, epochs=epochs, validation_split=test_split)
    hist = pd.DataFrame(history.history)
    hist["epoch"] = history.epoch
    info(hist)

    last_row = hist.loc[hist["epoch"] == epochs - 1].values[0]
    training_loss = last_row[0]
    validation_loss = last_row[1]
    info(f"Training loss: {training_loss}, validation loss: {validation_loss}")
    model.save("/tmp/model_service/test_model.h5")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname) - 4s %(message)s',
                        level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')
    main()
