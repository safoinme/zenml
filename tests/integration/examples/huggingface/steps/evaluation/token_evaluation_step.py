import tensorflow as tf
from datasets import DatasetDict
from transformers import (
    DataCollatorForTokenClassification,
    PreTrainedTokenizerBase,
    TFPreTrainedModel,
)

from zenml import step


@step
def token_evaluator(
    model: TFPreTrainedModel,
    tokenized_datasets: DatasetDict,
    tokenizer: PreTrainedTokenizerBase,
    dummy_run: bool = True,
    batch_size: int = 8,
) -> float:
    """Evaluate trained model on validation set."""
    # Needs to recompile because we are reloading model for evaluation
    model.compile(optimizer=tf.keras.optimizers.Adam())

    # Convert into tf dataset format
    validation_set = tokenized_datasets["validation"].to_tf_dataset(
        columns=["attention_mask", "input_ids", "labels"],
        shuffle=False,
        batch_size=batch_size,
        collate_fn=DataCollatorForTokenClassification(
            tokenizer, return_tensors="tf"
        ),
    )

    # Calculate loss
    if dummy_run:
        test_loss = model.evaluate(validation_set.take(10), verbose=1)
    else:
        test_loss = model.evaluate(validation_set, verbose=1)
    return test_loss
