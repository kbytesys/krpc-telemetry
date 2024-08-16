from abc import ABC, abstractmethod
from typing import Dict, Any, Set

import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from krpc_telemetry.telemetry import TelemetryType


class TelemetryStrategy(ABC):
    def __init__(self, collect_every_secs: int = 1):
        self._collect_every_secs = collect_every_secs
        self._lastMet = -1
        self._dataframe = pd.DataFrame()

    def collect_data(self, met: int, data: Dict[TelemetryType, Any]) -> None:
        if self._lastMet != -1 and self._collect_every_secs + self._lastMet > met:
            return

        self._lastMet = met
        self._collect_data(met, data)

    @abstractmethod
    def _collect_data(self, met: int, data: Dict[TelemetryType, Any]):
        pass

    @abstractmethod
    def get_telemetry_types(self) -> Set[TelemetryType]:
        pass

    @abstractmethod
    def _create_dataframe(self) -> DataFrame:
        pass

class OrbitalVelocityStrategy(TelemetryStrategy, ABC):
    def __init__(self):
        super().__init__(collect_every_secs=5)

        self.fig = None

    def _create_dataframe(self) -> DataFrame:
        result =  pd.DataFrame(columns=[TelemetryType.MET, TelemetryType.ORBITAL_SPEED])
        result.set_index(TelemetryType.MET, inplace=True)
        return result


    def get_telemetry_types(self) -> Set[TelemetryType]:
        return {TelemetryType.MET, TelemetryType.ORBITAL_SPEED}

    def _collect_data(self, met: int, data: Dict[TelemetryType, Any]):
        print("%s %s" % (TelemetryType.ORBITAL_SPEED, data[TelemetryType.ORBITAL_SPEED]))
        collected_data_dataframe = pd.DataFrame({
            TelemetryType.MET: met,
            TelemetryType.ORBITAL_SPEED: data[TelemetryType.ORBITAL_SPEED]
        }, index=[0])
        collected_data_dataframe.set_index(TelemetryType.MET, inplace=True)
        self._dataframe = pd.concat(
            [
                self._dataframe,
                collected_data_dataframe
            ]) if len(self._dataframe) else collected_data_dataframe

        if len(self._dataframe) == 1:
            self.fig, ax = self._dataframe.plot()
            self.fig.show()

        self.fig.batch_update()
