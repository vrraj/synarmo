#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Objective-C++ ownership boundary for the llama.cpp XCFramework.
@interface LlamaCppBridge : NSObject
- (BOOL)loadModelAtPath:(NSString *)path error:(NSError **)error;
- (void)unloadModel;
- (NSArray<NSDictionary<NSString *, id> *> *)suggestForText:(NSString *)text
                                                    context:(NSString *)context
                                                   choices:(NSInteger)choices
                                        candidateTokenCount:(NSInteger)candidateTokenCount
                                        candidateWordCount:(NSInteger)candidateWordCount
                                                temperature:(double)temperature
                                                       topP:(double)topP
                                                logprobPool:(NSInteger)logprobPool
                                                      error:(NSError **)error;
- (void)cancel;
@end

NS_ASSUME_NONNULL_END
