class RoomInformation:
    def __init__(self, room_number, sensor_id):
        self.room_number = room_number
        self.sensor_id = sensor_id
    def info(self):
        if self.room_number is None or self.sensor_id is None:
            return None
        return self.room_number, self.sensor_id
    def info_iter(self):
        if self.room_number is None or self.sensor_id is None:
            return None
        return ((self.room_number, id) for id in self.sensor_id)
