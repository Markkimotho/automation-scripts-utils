#!/usr/bin/env ruby
if ARGV.include?('--help') || ARGV.length != 1
  puts 'Usage: ruby script.rb FILE'
  exit ARGV.include?('--help') ? 0 : 2
end
file = ARGV.fetch(0)
abort('Input must be a file') unless File.file?(file)
puts File.size(file)
