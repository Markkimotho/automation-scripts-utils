#!/usr/bin/env ruby
# Compare exact UTF-8 CSV key values, preserving case and surrounding whitespace.
require 'csv'
require 'json'
require 'optparse'
require 'set'

def keys_from(path, column, limit)
  raise ArgumentError, 'input must be a regular file <= 32 MiB' unless File.file?(path) && File.size(path) <= 32 * 1024 * 1024
  keys, duplicates, rows = Set.new, Set.new, 0
  File.open(path, 'r:bom|utf-8') do |file|
    csv = CSV.new(file)
    header = csv.shift
    raise ArgumentError, 'header must contain unique nonempty names and the key column' unless header && header.all? { |x| x && !x.empty? } && header.uniq.size == header.size && header.include?(column)
    index = header.index(column)
    csv.each do |row|
      rows += 1
      raise ArgumentError, 'row limit exceeded' if rows > limit
      raise ArgumentError, 'row width mismatch or empty key' unless row.size == header.size && row[index] && !row[index].empty?
      key = row[index]
      duplicates.add(key) if keys.include?(key)
      keys.add(key)
    end
  end
  [keys, duplicates.to_a.sort, rows]
end

def main
  options = {limit: 100_000}
  parser = OptionParser.new do |opts|
    opts.banner = 'Usage: csv-key-reconcile --left old.csv --right new.csv --key id [--max-rows 100000]'
    opts.on('--left PATH') { |x| options[:left] = x }
    opts.on('--right PATH') { |x| options[:right] = x }
    opts.on('--key COLUMN') { |x| options[:key] = x }
    opts.on('--max-rows N', Integer) { |x| options[:limit] = x }
    opts.on('--help') { puts opts; return 0 }
  end
  parser.parse!
  raise ArgumentError, 'missing options or unexpected arguments' unless ARGV.empty? && [:left, :right, :key].all? { |x| options[x] && !options[x].empty? } && options[:limit].between?(1, 1_000_000)
  left, left_duplicates, left_rows = keys_from(options[:left], options[:key], options[:limit])
  right, right_duplicates, right_rows = keys_from(options[:right], options[:key], options[:limit])
  only_left, only_right = (left - right).to_a.sort, (right - left).to_a.sort
  puts JSON.pretty_generate({left_rows: left_rows, right_rows: right_rows, common: (left & right).size,
                            only_left: only_left, only_right: only_right,
                            duplicate_left: left_duplicates, duplicate_right: right_duplicates})
  [only_left, only_right, left_duplicates, right_duplicates].all?(&:empty?) ? 0 : 1
rescue OptionParser::ParseError, ArgumentError, IOError, SystemCallError, CSV::MalformedCSVError, EncodingError
  warn 'csv-key-reconcile: invalid arguments or unreadable/malformed UTF-8 CSV; require unique headers, nonempty keys and consistent row widths'
  2
end

exit main
