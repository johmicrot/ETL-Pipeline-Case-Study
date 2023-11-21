from kfp import dsl, compiler
import kfp.components as comp
from etl.config import Config as config

def new_file_trigger_op():
    return dsl.ContainerOp(
        name='new_file_trigger',
        image='new_file_trigger:1.0'
    )

def preprocessor_op():
    return dsl.ContainerOp(
        name='preprocessor',
        image='preprocessor:1.0'
    )

def train_model_op():
    return dsl.ContainerOp(
        name='train_model',
        image='train_model:1.0'
    )

def inference_op():
    return dsl.ContainerOp(
        name='inference',
        image='inference:1.0'
    )

@dsl.pipeline(
    name=config.PIPELINE_NAME,
    description='ETL Pipeline for TalpaSolutions'
)
def etl_pipeline():
    newfiletrigger = new_file_trigger_op()
    preprocessor = preprocessor_op().after(newfiletrigger)
    train_model = train_model_op().after(preprocessor)
    inference = inference_op().after(train_model)

if __name__ == '__main__':
    compiler.Compiler().compile(etl_pipeline, config.PIPELINE_MANIFEST_NAME)
