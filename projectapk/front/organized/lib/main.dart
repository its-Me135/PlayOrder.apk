import 'package:flutter/material.dart';
import 'package:device_preview/device_preview.dart';
import 'package:file_picker/file_picker.dart';

void main() {
  // WidgertsFlutterBinding.ensureInitialized();

  runApp(DevicePreview(enabled: true, builder: (context) => Home()));
}

class Home extends StatefulWidget {
  const Home({super.key});

  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  TextEditingController directoryController = TextEditingController();
  Widget build(BuildContext context) {
    return MaterialApp(
      useInheritedMediaQuery: true,
      locale: DevicePreview.locale(context),
      builder: DevicePreview.appBuilder,
      theme: ThemeData(
        // brightness: Brightness.light,
        scaffoldBackgroundColor: const Color.fromARGB(255, 20, 1, 44),
      ),
      home: Scaffold(
        resizeToAvoidBottomInset: false,
        appBar: AppBar(
          leading: Icon(Icons.playlist_play),
          title: Text(
            'Ordered Playlist ',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          backgroundColor: Colors.blueGrey,
        ),
        body: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                vertical: 25.0,
                horizontal: 8.0,
              ),
              child: Container(
                child: Center(
                  child: Column(
                    children: [
                      SizedBox(height: 10),
                      Row(
                        children: [
                          Image.asset(
                            'assets/images/logo.png',
                            width: 100,
                            height: 120,
                          ),
                          SizedBox(width: 20),
                          Expanded(
                            child: ShaderMask(
                              blendMode: BlendMode.srcIn,
                              shaderCallback: (Rect bounds) {
                                return LinearGradient(
                                  begin: Alignment
                                      .topRight, // Adjust based on 280deg
                                  end: Alignment.bottomLeft,
                                  colors: [
                                    Color(0xFF8430F2), // #8430f2
                                    Color(0xFF7022A1), // #7022a1
                                    Color(0xFF24F2E8), // #24f2e8
                                  ],
                                  stops: [
                                    0.0,
                                    0.44,
                                    1.0,
                                  ], // Your percentages: 0%, 44%, 100%
                                ).createShader(bounds);
                              },
                              child: Text(
                                'Automated files sequencing for Youtube local downloaded playlists',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Center(
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: const Color.fromARGB(255, 11, 182, 212),
                      width: 3.0,
                    ),
                    borderRadius: BorderRadius.circular(15.0),
                  ),
                  child: Card(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(15.0),
                    ),

                    color: Color.fromARGB(255, 20, 1, 44),
                    child: Container(
                      padding: const EdgeInsets.all(16.0),
                      height: 300,
                      child: Column(
                        children: [
                          Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                              'TARGET PLAYLIST URL :',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Color.fromARGB(255, 11, 182, 212),
                              ),
                            ),
                          ),
                          SizedBox(height: 10),

                          TextField(
                            style: TextStyle(color: Colors.white),
                            decoration: InputDecoration(
                              border: OutlineInputBorder(),

                              labelText: 'Enter PlayList URL',
                              labelStyle: TextStyle(color: Colors.white70),
                            ),
                          ),
                          SizedBox(height: 20),
                          Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                              'LOCAL DIRECTORY PATH :',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Color.fromARGB(255, 11, 182, 212),
                              ),
                            ),
                          ),
                          SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: directoryController,
                                  readOnly: true,
                                  style: TextStyle(color: Colors.white),
                                  decoration: InputDecoration(
                                    border: OutlineInputBorder(),
                                    labelText: 'Select Directory',
                                    labelStyle: TextStyle(
                                      color: Colors.white70,
                                    ),
                                  ),
                                ),
                              ),
                              SizedBox(width: 10),
                              ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Color.fromARGB(
                                    255,
                                    17,
                                    167,
                                    167,
                                  ),
                                ),
                                onPressed: () async {
                                  String? selectedDirectory = await FilePicker
                                      .platform
                                      .getDirectoryPath();
                                  if (selectedDirectory != null) {
                                    setState(() {
                                      directoryController.text =
                                          selectedDirectory;
                                    });
                                  }
                                },
                                child: Text(
                                  'Browse',
                                  style: TextStyle(color: Colors.black),
                                ),
                              ),
                            ],
                          ),
                          SizedBox(height: 20),
                          Row(
                            children: [
                              Text(
                                'DRY RUN (PREVIEW ONLY)',
                                style: TextStyle(
                                  fontSize: 18,
                                  color: Colors.white70,
                                ),
                              ),
                              SizedBox(width: 10),
                              Switch(
                                value: false,
                                onChanged: (bool value) {
                                  // Handle switch state change
                                },
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            //SizedBox(height: 20),
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color.fromARGB(255, 17, 167, 167),
                  ),

                  onPressed: () {
                    // Handle button press
                  },
                  child: Text(
                    'ORGANIZE & RENAME',
                    style: TextStyle(
                      fontSize: 23,
                      fontWeight: FontWeight.bold,
                      color: Colors.black,
                    ),
                  ),
                ),
              ),
            ),

            Expanded(
              child: Image.asset(
                'assets/images/mechanisim.png',
                width: 200,
                height: 100,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
