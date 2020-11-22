// 坐标系转换
// gcj02_to_bd09(point) 从火星坐标系 转换到 百度坐标系
// wgs84_to_gcj02(point)  从wgs坐标系 转换到 火星坐标系
// wgs84_to_bd09(point)  从wgs坐标系 到 火星坐标系

const x_pi = Math.PI * 3000.0 / 180.0;
const a = 6378245.0;   // 长半轴
const ee = 0.00669342162296594323;   // 偏心率平方

function _transformlat(lng, lat) {
    let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * Math.sqrt(Math.abs(lng));
    ret += (20.0 * Math.sin(6.0 * lng * Math.PI) + 20.0 * Math.sin(2.0 * lng * Math.PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(lat * Math.PI) + 40.0 * Math.sin(lat / 3.0 * Math.PI)) * 2.0 / 3.0;
    ret += (160.0 * Math.sin(lat / 12.0 * Math.PI) + 320 * Math.sin(lat * Math.PI / 30.0)) * 2.0 / 3.0;
    return ret
}

function _transformlng(lng, lat) {
    let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * Math.sqrt(Math.abs(lng));
    ret += (20.0 * Math.sin(6.0 * lng * Math.PI) + 20.0 * Math.sin(2.0 * lng * Math.PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(lng * Math.PI) + 40.0 * Math.sin(lng / 3.0 * Math.PI)) * 2.0 / 3.0;
    ret += (150.0 * Math.sin(lng / 12.0 * Math.PI) + 300.0 * Math.sin(lng / 30.0 * Math.PI)) * 2.0 / 3.0;
    return ret
}

// 从火星坐标系 转换到 百度坐标系
function gcj02_to_bd09(point) {
    let x = point.lng, y = point.lat;
    let z = Math.sqrt(x*x + y*y) + 0.00002 * Math.sin(y * x_pi);
    let theta = Math.atan2(y, x) + 0.000003 * Math.cos(x * x_pi);
    let lng = z * Math.cos(theta) + 0.0065;
    let lat = z * Math.sin(theta) + 0.006;
    return {
        lng: lng,
        lat: lat,
    }
}

// 从wgs坐标系 转换到 火星坐标系
function wgs84_to_gcj02(point) {
    let lng = point.lng;
    let lat = point.lat;
    let dlat = _transformlat(lng - 105.0, lat - 35.0);
    let dlng = _transformlng(lng - 105.0, lat - 35.0);
    let radlat = lat / 180.0 * Math.PI;
    let magic = Math.sin(radlat);
    magic = 1 - ee * magic * magic;
    let sqrtmagic = Math.sqrt(magic);
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * Math.PI);
    dlng = (dlng * 180.0) / (a / sqrtmagic * Math.cos(radlat) * Math.PI);
    let mglat = lat + dlat;
    let mglng = lng + dlng;
    return {
        lng: mglng,
        lat: mglat,
    }
}

// 从wgs坐标系 到 百度坐标系
function wgs84_to_bd09(point) {
    let poi = wgs84_to_gcj02(point);
    return gcj02_to_bd09(poi);
}
