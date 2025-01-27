from sqlalchemy import Integer, TypeDecorator

class IntEnumType(TypeDecorator):
    impl = Integer

    def __init__(self, enum_class):
        super().__init__()
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        return value.value if value is not None else None

    def process_result_value(self, value, dialect):
        return self.enum_class(value) if value is not None else None