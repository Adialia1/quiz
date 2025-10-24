/**
 * Expo Config Plugin to Force RTL at Native iOS Level
 *
 * This plugin modifies AppDelegate.m to force RTL before React Native loads.
 * This is Option B - native level RTL forcing.
 */

const { withAppDelegate } = require('@expo/config-plugins');

const RTL_CODE = `
  // Force RTL for Hebrew-only app - added by withRTL config plugin
  [[RCTI18nUtil sharedInstance] allowRTL:YES];
  [[RCTI18nUtil sharedInstance] forceRTL:YES];
`;

module.exports = function withRTL(config) {
  return withAppDelegate(config, (config) => {
    const { modResults } = config;
    let contents = modResults.contents;

    // Add import for RCTI18nUtil if not present
    if (!contents.includes('#import <React/RCTI18nUtil.h>')) {
      contents = contents.replace(
        /#import "AppDelegate.h"/,
        `#import "AppDelegate.h"\n#import <React/RCTI18nUtil.h>`
      );
    }

    // Add RTL forcing code in didFinishLaunchingWithOptions
    // Look for the method and add our code at the beginning
    if (!contents.includes('[[RCTI18nUtil sharedInstance] forceRTL:YES]')) {
      contents = contents.replace(
        /(- \(BOOL\)application:\(UIApplication \*\)application didFinishLaunchingWithOptions:\(NSDictionary \*\)launchOptions\s*\{)/,
        `$1${RTL_CODE}`
      );
    }

    modResults.contents = contents;
    return config;
  });
};
