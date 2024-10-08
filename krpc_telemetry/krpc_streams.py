import math
from time import sleep
from typing import Dict, Any, Callable

from krpc import Client
from krpc.services.spacecenter import Vessel
from krpc.stream import Stream

from krpc_telemetry.telemetry import TelemetryType
from krpc_telemetry.telemetry.processor import TelemetryProcessor


class KrpcTelemetryStream:
    def __init__(self, telemetry_type: TelemetryType, stream: Stream, rate: float,
                 transform_function: Callable[[Any], Any] = None) -> None:
        self._telemetry_type = telemetry_type
        self._stream = stream
        self._transform_function = transform_function
        # rate is a hertz value, we want one update per second
        self._stream.rate = rate

    def start(self) -> None:
        self._stream.start(False)

    @property
    def telemetry_type(self) -> TelemetryType:
        return self._telemetry_type

    @property
    def value(self) -> Any:
        if self._transform_function is not None:
            return self._transform_function(self._stream())
        return self._stream()

    def destroy(self) -> None:
        self._stream.remove()


class KrpcTelemetryStreamCollection:
    def __init__(self):
        self._streams = dict()

    def register_telemetry(self, telemetry: KrpcTelemetryStream) -> None:
        if telemetry.telemetry_type not in self._streams.keys():
            self._streams[telemetry.telemetry_type] = telemetry

    def has_telemetry(self, telemetry_type: TelemetryType) -> bool:
        return telemetry_type in self._streams.keys()

    def start_telemetries(self) -> None:
        for telemetry in self._streams.values():
            telemetry.start()
        # wait for first data
        sleep(2)

    def destroy_telemetries(self) -> None:
        for telemetry in self._streams.values():
            telemetry.destroy()
        self._streams.clear()

    def collect_data(self) -> Dict[TelemetryType, Any]:
        results = dict()
        for telemetry in self._streams.values():
            results[telemetry.telemetry_type] = telemetry.value

        return results


class KrpcTelemetryStreamFactory:
    def __init__(self, vessel: Vessel, conn: Client, default_rate: float = 1):
        self._vessel = vessel
        self._conn = conn
        self._default_rate = default_rate

        self._orbit_reference_fight = None
        self._vessel_reference_flight = None

    def create(self, telemetry_type: TelemetryType) -> KrpcTelemetryStream:
        if not self._orbit_reference_fight:
            self._orbit_reference_fight = self._vessel.flight(self._vessel.orbit.body.reference_frame)
            self._vessel_reference_flight = self._vessel.flight(self._vessel.reference_frame)

        if telemetry_type == TelemetryType.MET:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._vessel, 'met'),
                self._default_rate,
                lambda value: math.floor(value)
            )

        if telemetry_type == TelemetryType.ORBITAL_SPEED:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._vessel.orbit, 'speed'),
                self._default_rate,
                lambda value: round(value, 1)
            )

        if telemetry_type == TelemetryType.SURFACE_SPEED:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'speed'),
                self._default_rate,
                lambda value: round(value, 1)
            )

        if telemetry_type == TelemetryType.SURFACE_HORIZONTAL_SPEED:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'horizontal_speed'),
                self._default_rate,
                lambda value: round(value, 1)
            )

        if telemetry_type == TelemetryType.SURFACE_VERTICAL_SPEED:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'vertical_speed'),
                self._default_rate,
                lambda value: round(value, 1)
            )

        if telemetry_type == TelemetryType.ORBITAL_APOAPSIS:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._vessel.orbit, 'apoapsis_altitude'),
                self._default_rate,
                lambda value: round(value/1000, 0)
            )

        if telemetry_type == TelemetryType.ORBITAL_PERIAPSIS:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._vessel.orbit, 'periapsis_altitude'),
                self._default_rate,
                lambda value: round(value/1000, 0)
            )

        if telemetry_type == TelemetryType.G_FORCE:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'g_force'),
                self._default_rate,
                lambda value: round(value, 1)
            )

        if telemetry_type == TelemetryType.CENTER_OF_MASS:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'center_of_mass'),
                self._default_rate
            )

        if telemetry_type == TelemetryType.ATMOSPHERE_DENSITY:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'atmosphere_density'),
                self._default_rate
            )

        if telemetry_type == TelemetryType.DYNAMIC_PRESSURE:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'dynamic_pressure'),
                self._default_rate
            )

        if telemetry_type == TelemetryType.STATIC_PRESSURE:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'static_pressure'),
                self._default_rate
            )

        if telemetry_type == TelemetryType.AERODYNAMIC_FORCE:
            return KrpcTelemetryStream(
                telemetry_type,
                self._conn.add_stream(getattr, self._orbit_reference_fight, 'aerodynamic_force'),
                self._default_rate
            )

        raise ValueError("Telemetry %s unknown" % telemetry_type)


def init_streams_from_telemetry_processor(processor: TelemetryProcessor,
                                          factory: KrpcTelemetryStreamFactory) -> KrpcTelemetryStreamCollection:
    result = KrpcTelemetryStreamCollection()
    for telemetry_type in processor.get_telemetry_types():
        result.register_telemetry(
            factory.create(telemetry_type)
        )
    return result
