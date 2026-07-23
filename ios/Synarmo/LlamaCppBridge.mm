#import "LlamaCppBridge.h"

#if SYNARMO_LLAMA_CPP
#import <llama/llama.h>

#import <algorithm>
#import <atomic>
#import <cmath>
#import <string>
#import <unordered_set>
#import <vector>
#endif

static NSString * const SynarmoInferenceErrorDomain = @"SynarmoInference";

namespace {

NSError *SynarmoInferenceError(NSString *message) {
    return [NSError errorWithDomain:SynarmoInferenceErrorDomain
                               code:1
                           userInfo:@{NSLocalizedDescriptionKey: message}];
}

#if SYNARMO_LLAMA_CPP
struct RankedToken {
    llama_token id;
    float logprob;
    std::string piece;
};

std::string TokenPiece(const llama_vocab *vocab, llama_token token) {
    std::vector<char> buffer(128);
    int32_t length = llama_token_to_piece(vocab, token, buffer.data(), (int32_t) buffer.size(), 0, false);
    if (length < 0) {
        buffer.resize((size_t) -length);
        length = llama_token_to_piece(vocab, token, buffer.data(), (int32_t) buffer.size(), 0, false);
    }
    return length > 0 ? std::string(buffer.data(), (size_t) length) : "";
}

std::vector<llama_token> Tokenize(const llama_vocab *vocab, const std::string &text) {
    int32_t count = llama_tokenize(vocab, text.c_str(), (int32_t) text.size(), nullptr, 0, true, false);
    if (count >= 0) {
        return {};
    }
    std::vector<llama_token> tokens((size_t) -count);
    count = llama_tokenize(vocab, text.c_str(), (int32_t) text.size(), tokens.data(), (int32_t) tokens.size(), true, false);
    if (count < 0) {
        return {};
    }
    tokens.resize((size_t) count);
    return tokens;
}

bool HasStopCharacter(const std::string &piece) {
    return piece.find_first_of("\n.!?") != std::string::npos;
}

NSString *NormalizedCandidate(const std::string &value, NSInteger maxWords) {
    NSString *candidate = [[NSString alloc] initWithBytes:value.data()
                                                   length:value.size()
                                                 encoding:NSUTF8StringEncoding];
    if (candidate == nil) {
        return @"";
    }
    candidate = [candidate stringByReplacingOccurrencesOfString:@"\n" withString:@" "];
    candidate = [candidate stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    while ([candidate hasPrefix:@":"]) {
        candidate = [[candidate substringFromIndex:1] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    }
    candidate = [candidate stringByTrimmingCharactersInSet:[NSCharacterSet characterSetWithCharactersInString:@"\"'` ,;:"]];
    NSArray<NSString *> *words = [candidate componentsSeparatedByCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    NSMutableArray<NSString *> *nonEmpty = [NSMutableArray array];
    for (NSString *word in words) {
        if (word.length > 0) {
            [nonEmpty addObject:word];
            if (maxWords > 0 && nonEmpty.count >= (NSUInteger) maxWords) {
                break;
            }
        }
    }
    return [[nonEmpty componentsJoinedByString:@" "] stringByTrimmingCharactersInSet:[NSCharacterSet characterSetWithCharactersInString:@" ,;:"]];
}
#endif
}

@interface LlamaCppBridge () {
#if SYNARMO_LLAMA_CPP
    llama_model *_model;
    llama_context *_context;
    const llama_vocab *_vocab;
    std::atomic_bool _cancelled;
#endif
}
@end

@implementation LlamaCppBridge

- (void)dealloc {
#if SYNARMO_LLAMA_CPP
    if (_context != nullptr) {
        llama_free(_context);
    }
    if (_model != nullptr) {
        llama_model_free(_model);
    }
#endif
}

- (BOOL)loadModelAtPath:(NSString *)path error:(NSError **)error {
#if SYNARMO_LLAMA_CPP
    @synchronized (self) {
        _cancelled.store(false);
        if (_context != nullptr) {
            llama_free(_context);
            _context = nullptr;
        }
        if (_model != nullptr) {
            llama_model_free(_model);
            _model = nullptr;
        }

        llama_backend_init();
        llama_model_params modelParameters = llama_model_default_params();
        modelParameters.n_gpu_layers = 999;
        _model = llama_model_load_from_file(path.fileSystemRepresentation, modelParameters);
        if (_model == nullptr) {
            if (error != nullptr) {
                *error = SynarmoInferenceError(@"Unable to load the downloaded GGUF model.");
            }
            return NO;
        }

        llama_context_params contextParameters = llama_context_default_params();
        contextParameters.n_ctx = 2048;
        contextParameters.n_batch = 512;
        contextParameters.n_ubatch = 512;
        _context = llama_init_from_model(_model, contextParameters);
        if (_context == nullptr) {
            llama_model_free(_model);
            _model = nullptr;
            if (error != nullptr) {
                *error = SynarmoInferenceError(@"Unable to create a llama.cpp inference context.");
            }
            return NO;
        }
        _vocab = llama_model_get_vocab(_model);
        return YES;
    }
#else
    if (error != NULL) {
        *error = [NSError errorWithDomain:SynarmoInferenceErrorDomain
                                     code:1
                                 userInfo:@{NSLocalizedDescriptionKey: @"llama.cpp XCFramework is not linked. See ios/Docs/llama-cpp-integration.md."}];
    }
    return NO;
#endif
}

- (void)unloadModel {
#if SYNARMO_LLAMA_CPP
    @synchronized (self) {
        _cancelled.store(true);
        if (_context != nullptr) {
            llama_free(_context);
            _context = nullptr;
        }
        if (_model != nullptr) {
            llama_model_free(_model);
            _model = nullptr;
        }
        _vocab = nullptr;
    }
#endif
}

- (NSArray<NSDictionary<NSString *,id> *> *)suggestForText:(NSString *)text
                                                    context:(NSString *)context
                                                   choices:(NSInteger)choices
                                        candidateTokenCount:(NSInteger)candidateTokenCount
                                        candidateWordCount:(NSInteger)candidateWordCount
                                                temperature:(double)temperature
                                                      topP:(double)topP
                                                logprobPool:(NSInteger)logprobPool
                                                      error:(NSError **)error {
#if SYNARMO_LLAMA_CPP
    @synchronized (self) {
        if (_context == nullptr || _model == nullptr || _vocab == nullptr) {
            if (error != nullptr) {
                *error = SynarmoInferenceError(@"Load the local model before requesting suggestions.");
            }
            return @[];
        }
        _cancelled.store(false);
        std::string prompt = std::string(context.UTF8String ?: "") + "\n\nLive message:\n" + std::string(text.UTF8String ?: "");
        std::vector<llama_token> promptTokens = Tokenize(_vocab, prompt);
        if (promptTokens.empty()) {
            if (error != nullptr) {
                *error = SynarmoInferenceError(@"Unable to tokenize the current message.");
            }
            return @[];
        }
        const NSInteger maxContinuationTokens = MAX(1, candidateTokenCount);
        const size_t maxPromptTokens = 2048 - (size_t) maxContinuationTokens - 1;
        if (promptTokens.size() > maxPromptTokens) {
            promptTokens.erase(promptTokens.begin(), promptTokens.end() - maxPromptTokens);
        }

        auto decodeTokens = ^bool(const std::vector<llama_token> &tokens) {
            for (size_t offset = 0; offset < tokens.size(); offset += 512) {
                if (_cancelled.load()) {
                    return false;
                }
                const int32_t count = (int32_t) std::min<size_t>(512, tokens.size() - offset);
                llama_batch batch = llama_batch_get_one(const_cast<llama_token *>(tokens.data() + offset), count);
                if (llama_decode(_context, batch) != 0) {
                    return false;
                }
            }
            return true;
        };

        llama_kv_self_clear(_context);
        if (!decodeTokens(promptTokens)) {
            if (error != nullptr) {
                *error = SynarmoInferenceError(_cancelled.load() ? @"Suggestion request cancelled." : @"llama.cpp could not evaluate the prompt.");
            }
            return @[];
        }
        const llama_pos promptTokenCount = (llama_pos) promptTokens.size();
        float *logits = llama_get_logits_ith(_context, -1);
        const int32_t vocabSize = llama_vocab_n_tokens(_vocab);
        if (logits == nullptr || vocabSize <= 0) {
            if (error != nullptr) {
                *error = SynarmoInferenceError(@"llama.cpp did not return next-token logits.");
            }
            return @[];
        }
        float maximum = logits[0];
        for (int32_t index = 1; index < vocabSize; ++index) {
            if (_cancelled.load()) {
                return @[];
            }
            maximum = std::max(maximum, logits[index]);
        }
        double sum = 0;
        for (int32_t index = 0; index < vocabSize; ++index) {
            if (_cancelled.load()) {
                return @[];
            }
            sum += std::exp((double) logits[index] - maximum);
        }
        const float logSum = maximum + (float) std::log(sum);
        std::vector<RankedToken> ranked;
        ranked.reserve((size_t) vocabSize);
        for (int32_t index = 0; index < vocabSize; ++index) {
            if (_cancelled.load()) {
                return @[];
            }
            const std::string piece = TokenPiece(_vocab, index);
            if (!piece.empty()) {
                ranked.push_back({index, logits[index] - logSum, piece});
            }
        }
        const size_t pool = (size_t) std::max<NSInteger>(logprobPool, choices);
        std::partial_sort(ranked.begin(), ranked.begin() + std::min(pool, ranked.size()), ranked.end(), [](const RankedToken &left, const RankedToken &right) {
            return left.logprob > right.logprob;
        });
        ranked.resize(std::min(pool, ranked.size()));

        std::vector<RankedToken> starters;
        std::unordered_set<std::string> seen;
        for (const RankedToken &item : ranked) {
            NSString *normalized = NormalizedCandidate(item.piece, 1);
            if (normalized.length == 0 || [normalized rangeOfCharacterFromSet:[NSCharacterSet letterCharacterSet]].location == NSNotFound) {
                continue;
            }
            std::string key = normalized.lowercaseString.UTF8String;
            if (seen.insert(key).second) {
                starters.push_back(item);
                if (starters.size() >= (size_t) choices) {
                    break;
                }
            }
        }

        NSMutableArray<NSDictionary<NSString *, id> *> *results = [NSMutableArray array];
        for (const RankedToken &starter : starters) {
            if (_cancelled.load()) {
                break;
            }
            // Keep the prompt in the KV cache. Remove only the previous candidate
            // branch, then decode this candidate's continuation token by token.
            if (!llama_kv_self_seq_rm(_context, 0, promptTokenCount, -1)) {
                if (error != nullptr) {
                    *error = SynarmoInferenceError(@"Unable to reset the candidate KV cache branch.");
                }
                break;
            }
            std::vector<llama_token> nextTokens = {starter.id};
            if (!decodeTokens(nextTokens)) {
                break;
            }
            std::string completion = starter.piece;
            for (NSInteger generated = 1; generated < maxContinuationTokens; ++generated) {
                if (_cancelled.load()) {
                    break;
                }
                float *nextLogits = llama_get_logits_ith(_context, -1);
                if (nextLogits == nullptr) {
                    break;
                }
                llama_token next = 0;
                for (int32_t index = 1; index < vocabSize; ++index) {
                    if (_cancelled.load()) {
                        break;
                    }
                    if (nextLogits[index] > nextLogits[next]) {
                        next = index;
                    }
                }
                if (_cancelled.load()) {
                    break;
                }
                if (llama_vocab_is_eog(_vocab, next)) {
                    break;
                }
                const std::string piece = TokenPiece(_vocab, next);
                if (piece.empty() || HasStopCharacter(piece)) {
                    break;
                }
                completion += piece;
                nextTokens[0] = next;
                if (!decodeTokens(nextTokens)) {
                    break;
                }
            }
            NSString *candidate = NormalizedCandidate(completion, candidateWordCount);
            if (candidate.length > 0) {
                [results addObject:@{ @"text": candidate, @"score": @(starter.logprob) }];
            }
        }
        return results;
    }
#else
    if (error != NULL) {
        *error = [NSError errorWithDomain:SynarmoInferenceErrorDomain
                                     code:1
                                 userInfo:@{NSLocalizedDescriptionKey: @"llama.cpp candidate generation is not linked yet."}];
    }
    return @[];
#endif
}

- (void)cancel {
#if SYNARMO_LLAMA_CPP
    _cancelled.store(true);
#endif
}

@end
