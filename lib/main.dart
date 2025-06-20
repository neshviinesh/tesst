import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart'; // For continuous location tracking

void main() {
  runApp(const MyApp()); // Entry point of the app
}

/// The root widget of the Flutter app
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Banner(
        message: 'FlexZ',
        location: BannerLocation.topEnd,
        child: const FinalView(), // Main screen of the app
      ),
    );
  }
}

/// The main screen of the app (StatefulWidget to handle state changes)
class FinalView extends StatefulWidget {
  const FinalView({super.key});

  @override
  State<FinalView> createState() => _FinalViewState();
}

/// State class for `FinalView`
class _FinalViewState extends State<FinalView> {
  Stream<Position>? _positionStream;

  @override
  void initState() {
    super.initState();
    startLocationStream(); // Start continuous location updates
  }

  /// Starts listening to the user's location and prints it continuously
  void startLocationStream() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    LocationPermission permission = await Geolocator.checkPermission();

    if (!serviceEnabled) {
      print("❌ Location services are disabled.");
      return;
    }

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        print("❌ Location permissions are denied.");
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      print("❌ Location permissions are permanently denied.");
      return;
    }

    // Start the stream
    _positionStream = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Notify only if user moves 10 meters
      ),
    );

    _positionStream!.listen((Position position) {
      print("📍 Latitude: ${position.latitude}, Longitude: ${position.longitude}");
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('User Location')),
      body: const Center(
        child: Text(
          'Listening to continuous location...\nCheck console output.',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
