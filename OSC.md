# OSC API notes

See below notes on interfacing with LG 360 CAM's OSC API.

**API endpoint**: http://192.168.43.1:6624/osc/commands/execute

## Setting coordinates

```
{
	"name": "camera.setOptions",
	"parameters": {
		"options": {
			"gpsInfo": {
				"lat": -33.000,
				"lng": 151.000,
				"_altitude": 0
			}
		}
	}
}
```

## Setting date/time

```
{
	"name": "camera.setOptions",
	"parameters": {
		"options": {
			"dateTimeZone": "2020:11:07 00:00:00+10:00"
		}
	}
}
```

## Set capture mode
TODO

## Begin capture
TODO

## Stop capture
TODO

## Single photo capture
```
{
	"name": "camera.takePicture",
	"parameters": {
		"sessionId": "SID_0001"
	}
}
```

## List photos

```
{
	"name": "camera.listFiles",
	"parameters": {
		"fileType": "image",
		"entryCount": 200
	}
}
```

## Get photo

```
{
	"name": "camera.getImage",
	"parameters": {
		"fileUri": "\/media\/e\/DCIM\/Camera\/<from camera.listFiles>.jpg"
	}
}
```