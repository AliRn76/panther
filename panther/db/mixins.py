class SerializableModel:

    serializable_fields: tuple = ()

    def model_dump(self) -> dict:
        if self.serializable_fields:
            return {field: getattr(self, field) for field in self.serializable_fields}

        return {field: value for field, value in self.__dict__.items() if not field.startswith("_")}
