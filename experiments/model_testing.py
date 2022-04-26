import tensorflow as tf
import os
import pandas as pd
from pprint import pprint
import logging
import multiprocessing
from logging import info, error
from sklearn.preprocessing import MinMaxScaler
from tensorboard.plugins.hparams import api as hp

# Global params
FEATURE_FIELDS: list = [
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
LABEL_FIELD: str = "SOIL_TEMPERATURE_0_TO_01_M_BELOW_SURFACE_KELVIN"
USE_CUDA: bool = True


def cuda_exports():
    # Set CUDA and CUPTI paths
    os.environ['CUDA_HOME'] = '/usr/local/cuda'
    os.environ['PATH']= '/usr/local/cuda/bin:$PATH'
    os.environ['CPATH'] = '/usr/local/cuda/include:$CPATH'
    os.environ['LIBRARY_PATH'] = '/usr/local/cuda/lib64:$LIBRARY_PATH'
    os.environ['LD_LIBRARY_PATH'] = '/usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH'
    os.environ['LD_LIBRARY_PATH'] = '/usr/local/cuda/lib64:$LD_LIBRARY_PATH'
    os.environ['CUDA_VISIBLE_DEVICES'] = '2'


def load_data() -> (pd.DataFrame, pd.DataFrame):
    csv_path: str = f"/s/paper/a/tmp/noaa_nam_normalized.csv"
    all_df: pd.DataFrame = pd.read_csv(csv_path, header=0)
    # test_df = all_df.sample(frac=0.2, axis=0)
    # train_df = all_df.drop(index=test_df.index)
    # train_features = train_df[FEATURE_FIELDS]
    # train_labels = train_df[LABEL_FIELD]
    # test_features = test_df[FEATURE_FIELDS]
    # test_labels = test_df[LABEL_FIELD]
    return all_df[FEATURE_FIELDS], all_df[LABEL_FIELD]

def session(session_num, batch_size, hl1_num_unit, hl2_num_unit, learning_rate):

    import tensorflow as tf
    import os
    import pandas as pd
    from pprint import pprint
    import logging
    import multiprocessing
    from logging import info, error

    csv_path: str = f"/s/paper/a/tmp/noaa_nam_normalized.csv"
    all_df: pd.DataFrame = pd.read_csv(csv_path, header=0)
    features = all_df[FEATURE_FIELDS]
    labels = all_df[LABEL_FIELD]

    info(f"Running session {session_num}: batch size = {batch_size}, hl1 units = {hl1_num_unit}, hl2 units = {hl2_num_unit}, learning rate = {learning_rate}")
    run_name = f"run_{session_num}_{batch_size}_{hl1_num_unit}_{hl2_num_unit}_{str(learning_rate).replace('.','')}"

    # Stops the model's training if it converges
    early_stop_callback = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",  # Quantity to be monitored.
        min_delta=0.001,  # Minimum change in the monitored quantity to qualify as an improvement, i.e. an absolute change of less than min_delta, will count as no improvement.
        patience=1,  # Number of epochs with no improvement after which training will be stopped.
        verbose=1,  # Verbosity mode, 0 or 1. Mode 0 is silent, and mode 1 displays messages when the callback takes an action.
        mode="min",  # In min mode, training will stop when the quantity monitored has stopped decreasing.
        baseline=0.03,  # Baseline value for the monitored quantity. Training will stop if the model doesn't show improvement over the baseline.
        restore_best_weights=True,  # Whether to restore model weights from the epoch with the best value of the monitored quantity.
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate)
    epochs = 10
    activation = tf.nn.relu

    model = tf.keras.Sequential([
        tf.keras.Input(shape=(len(FEATURE_FIELDS))),
        tf.keras.layers.Dense(units=hl1_num_unit, activation=activation, name="hl_1"),
        tf.keras.layers.Dense(units=hl2_num_unit, activation=activation, name="hl_2"),
        tf.keras.layers.Dense(units=1, name="output_layer")
    ])

    model.compile(loss="mean_squared_error", optimizer=optimizer)
    model.summary()

    # Fit the model to the data
    history = model.fit(
        x=features,
        y=labels,
        shuffle=True,
        validation_split=0.2,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[
            early_stop_callback
        ]
    )
    hist = pd.DataFrame(history.history)
    info(hist)
    hist.to_csv(f"/s/chopin/b/grad/cacaleb/{run_name}.csv", index=False)
    model.save(f"/s/chopin/b/grad/cacaleb/{run_name}.h5")


# Strictly for testing
def main():
    features, labels = load_data()

    cuda_exports()

    # Hyperparameter search
    batch_sizes = [64]
    hl1_num_units = [16, 32, 64]
    hl2_num_units = [16, 32, 64]
    learning_rates = [0.0001, 0.001, 0.01]

    session_num = 0
    for batch_size in batch_sizes:
        for hl1_num_unit in hl1_num_units:
            for hl2_num_unit in hl2_num_units:
                for learning_rate in learning_rates:
                    process_eval = multiprocessing.Process(target=session, args=(session_num, batch_size, hl1_num_unit, hl2_num_unit, learning_rate))
                    process_eval.start()
                    process_eval.join()
                    session_num += 1


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname) - 4s %(message)s',
                        level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')
    main()
