import types


def extract_object(obj: types.ExtractableObjects, config: types.ExtractionConfig):
    if isinstance(obj, types.TableToExtract):
        # Extract table-specific information
        pass
    elif isinstance(obj, types.ObjectsToExtract):
        # Extract object-specific information
        pass
