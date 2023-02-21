# Ambilight Hyperion for kodi using protobuf
This addon uses Kodi `render capture` to send images to Hyperion server using protobuf protocol
- https://alwinesch.github.io/group__python__xbmc___render_capture.html
- https://github.com/hyperion-project/hyperion.ng/tree/master/libsrc/protoserver

## protobuf vs flatbuffers
The average execution time:
|              |            Seconds            |
|--------------|-------------------------------|
|protobuf      |`0.0001062154769897461`        |
|flatbuffers   |`0.0308110272442853`           |

## flatbuffers project
- https://github.com/CPVprogrammer/kodi-hyperion-flatbuffers
