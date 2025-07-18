import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { WebView } from 'react-native-webview';

const VIDEO_FEED_URL = 'http://10.102.99.142:8090/video_feed'; // Replace with your computer's IP

export default function CameraFeedScreen() {
  return (
    <View style={styles.container}>
      <WebView
        source={{ uri: VIDEO_FEED_URL }}
        style={styles.webview}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        allowsInlineMediaPlayback={true}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  webview: {
    flex: 1,
    width: Dimensions.get('window').width,
    height: Dimensions.get('window').height,
  },
});
