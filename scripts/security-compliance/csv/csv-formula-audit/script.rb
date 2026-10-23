#!/usr/bin/env ruby
# Inspect cell prefixes without evaluating spreadsheet content or exposing values.
begin
  require 'csv'
  require 'json'
  require 'optparse'
rescue LoadError
  warn 'csv-formula-audit: Ruby csv, json and optparse libraries are required'
  exit 2
end

def main
  options = {}
  parser = OptionParser.new do |opts|
    opts.banner = 'Usage: csv-formula-audit --input data.csv'
    opts.on('--input PATH') { |value| options[:input] = value }
    opts.on('--help') { puts opts; return 0 }
  end
  parser.parse!
  path = options[:input]
  raise ArgumentError unless ARGV.empty? && path && File.file?(path) && File.size(path) <= 16 * 1024 * 1024
  rows, cells, count, findings = 0, 0, 0, []
  data = File.open(path, 'rb') { |file| file.read(16 * 1024 * 1024 + 1) || '' }
  raise ArgumentError if data.bytesize > 16 * 1024 * 1024
  data.force_encoding(Encoding::UTF_8)
  raise ArgumentError unless data.valid_encoding?
  data = data.delete_prefix("\uFEFF")
  CSV.new(data).each do |row|
    rows += 1
    raise ArgumentError if rows > 100_000
    row.each_with_index do |value, column|
      cells += 1
      raise ArgumentError if cells > 1_000_000
      next if value.nil? || value.empty?
      raise ArgumentError unless value.valid_encoding?
      normalized = value.unicode_normalize(:nfkc)
      first = normalized.lstrip[0]
      if ["\t", "\r", "\n"].include?(normalized[0]) || ['=', '+', '-', '@'].include?(first)
        count += 1
        findings << {row: rows, column: column + 1, reason: 'formula-like-prefix'} if findings.size < 1000
      end
    end
  end
  puts JSON.pretty_generate({rows: rows, cells: cells, finding_count: count, findings: findings, truncated: count > findings.size})
  count.positive? ? 1 : 0
rescue OptionParser::ParseError, ArgumentError, IOError, SystemCallError, CSV::MalformedCSVError, EncodingError
  warn 'csv-formula-audit: invalid arguments, malformed UTF-8 CSV or resource limit; expected a file <=16 MiB, <=100000 rows / 1000000 cells'
  2
end
exit main
