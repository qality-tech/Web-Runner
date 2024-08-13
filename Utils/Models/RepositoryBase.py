from contextlib import suppress

import numpy as np
import pandas as pd

from typing import TypeVar, Generic, List, Callable, Any

T = TypeVar('T')


class Base(Generic[T]):
    df = None
    identifier = None
    model = None

    @classmethod
    def set_dataframe(cls, value: pd.DataFrame) -> None:
        cls.df = value

    @classmethod
    def get_base(cls, **kwargs):
        df = cls.df if 'df' not in kwargs else kwargs['df']
        condition = kwargs['get_condition'] if 'get_condition' in kwargs else 'and'
        conditions = []
        fields_dict = cls.model.get_fields_dict()
        for key, value in kwargs.items():
            if key in ['get_condition', 'update_column', 'update_value']:
                continue
            key = fields_dict[key]
            c_value = value if type(value) == list else [value]
            conditions.append((key, c_value))
        if len(conditions) == 0:
            return df
        if condition == 'and':
            result = df[np.logical_and.reduce([(df[c[0]].isin(c[1])) for c in conditions])]
        else:
            result = df[np.logical_or.reduce([(df[c[0]].isin(c[1])) for c in conditions])]
        return result

    @classmethod
    def get(cls, **kwargs) -> T | None:
        with suppress(Exception):
            return cls.model(cls.get_base(**kwargs).iloc[0].to_dict())
        return None

    @classmethod
    def get_all(cls, **kwargs) -> List[T] | None:
        with suppress(Exception):
            return list(cls.model(row) for row in cls.get_base(**kwargs).to_dict(orient="records"))
        return None

    @classmethod
    def update(cls, **kwargs) -> List[T] | None:
        with suppress(Exception):
            filtered_df = cls.get_base(**kwargs)
            fields_dict = cls.model.get_fields_dict()
            update_column = kwargs['update_column'] if 'update_column' in kwargs else None
            if type(update_column) == list:
                for i, uc in enumerate(update_column):
                    with suppress(Exception,):
                        update_column[i] = fields_dict[uc]
            elif update_column in fields_dict:
                update_column = fields_dict[update_column]
            update_value = kwargs['update_value'] if 'update_value' in kwargs else None
            cls.df.loc[cls.df.index.isin(filtered_df.index.values), update_column] = update_value
            updated_df = cls.df.loc[cls.df.index.isin(filtered_df.index.values)]
            return list(cls.model(row) for row in updated_df.to_dict(orient="records"))
        return None

    @classmethod
    def to_model(cls, series: pd.Series) -> T:
        return cls.model(series.to_dict())

    @classmethod
    def to_list_model(cls, df: pd.DataFrame) -> T:
        return list(cls.model(row) for row in df.to_dict(orient="records"))
