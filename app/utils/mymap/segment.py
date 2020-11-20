class Segment:

    def __init__(self, point1, point2):
        self.ends = (point1, point2)

    def to_json(self):
        _l = []
        for _p in self.ends:
            _l.append(_p.to_json())
        return {
            'ends': _l
        }

    def __str__(self):
        return str(self.to_json())

    def __repr__(self):
        return 'Segment: {}'.format(str(self))

    def get_length(self):
        return self.ends[0].distance(self.ends[1])
